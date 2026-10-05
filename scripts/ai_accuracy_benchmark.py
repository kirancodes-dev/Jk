"""
AI domain-classification accuracy benchmark for SIH 26043.

Data splits (fixed; never tune on TEST)
---------------------------------------
* TEST  - the 198 labelled reports below (11 domains x 18; English, Hindi,
          Hinglish). Frozen since commit cc2bbfc: their SHA-256 fingerprint is
          checked in CI, so they cannot be edited to inflate the score. They
          are held out: no keyword, weight or threshold is chosen by looking
          at TEST results.
* TRAIN - scripts/ai_eval/train_dev.jsonl, every item whose position within
          its domain is not a multiple of 4 (330 items). Used to build and
          debug the lexicon.
* DEV   - the remaining quarter of train_dev.jsonl (110 items, every 4th item
          per domain). Used to decide which changes to keep and to calibrate
          the human-review confidence threshold.

TRAIN/DEV were written separately from TEST (different scenarios, more
SMS-style and Devanagari text) and CI checks that no report appears in both.

Every item runs through the real
backend.app.services.ai.classification_service classifier (no mocking).
The run reports accuracy per split, a per-domain breakdown, the confusion
matrix, an ablation table and the review-threshold calibration, and writes
ai_accuracy_report.json.

Run:        PYTHONPATH=. python scripts/ai_accuracy_benchmark.py
Calibrate:  PYTHONPATH=. python scripts/ai_accuracy_benchmark.py --calibrate
"""
import argparse
import hashlib
import json
import subprocess
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, ".")

from backend.app.core.config import settings  # noqa: E402
from backend.app.services.ai.embedding_service import embedding_service  # noqa: E402
from backend.app.services.ai.classification_service import (  # noqa: E402
    _COMPILED_LEXICON, _normalise,
    AIClassificationService, REVIEW_CONFIDENCE_THRESHOLD,
)

TRAIN_DEV_PATH = Path(__file__).resolve().parent / "ai_eval" / "train_dev.jsonl"
DEV_EVERY = 4
# Commit whose classifier produced the previous published figure (68.2% on TEST).
V2_REFERENCE_COMMIT = "cc2bbfc"

# ---------------------------------------------------------------------------
# Labeled evaluation set. Each domain gets ~18 items: varied villages/districts,
# varied phrasing (formal complaint, terse SMS-style, Hindi, Hinglish), so the
# classifier is exercised the way real citizen submissions actually read —
# not keyword-stuffed test fixtures.
# ---------------------------------------------------------------------------

DISTRICTS = [
    "Ranchi", "Dhanbad", "Bokaro", "Hazaribagh", "Giridih", "Deoghar", "Godda",
    "Sahibganj", "Pakur", "Dumka", "Jamtara", "Koderma", "Chatra", "Palamu",
    "Garhwa", "Latehar", "Lohardaga", "Gumla", "Simdega", "West Singhbhum",
    "East Singhbhum", "Saraikela", "Khunti", "Ramgarh",
]


def d(i):
    return DISTRICTS[i % len(DISTRICTS)]


SAMPLES = []


def add(domain, title, description, district_idx):
    SAMPLES.append({
        "title": title,
        "description": description,
        "district": d(district_idx),
        "true_domain": domain,
    })


# ---- Water Resources (18) ----
add("Water Resources", "Handpump Dry for Three Weeks in Tola", "The only handpump serving our tola has gone completely dry since the water table dropped. Women are walking 3 km to fetch drinking water daily.", 0)
add("Water Resources", "Fluoride Contamination Reported in Village Well", "Government testing confirmed high fluoride levels in our drinking water well. Several children have developed dental fluorosis and joint pain.", 1)
add("Water Resources", "बोरवेल से गंदा पानी आ रहा है", "गांव के बोरवेल का पानी पीला और बदबूदार आ रहा है। पीने लायक नहीं है, तुरंत जांच कराएं।", 2)
add("Water Resources", "Irrigation Canal Blocked by Silt Before Monsoon", "The main irrigation canal feeding 200 acres of farmland is choked with silt and won't be usable when the monsoon paddy transplant season starts.", 3)
add("Water Resources", "No Piped Water Supply Despite Jal Jeevan Mission Pipeline", "Pipeline was laid two years ago under Jal Jeevan Mission but no water has ever flowed through it. Households still depend on a single distant borewell.", 4)
add("Water Resources", "chapakal kharab ho gaya hai", "hamare mohalla ka chapakal ek mahine se kharab hai, paani lene ke liye dusre gaon jaana padta hai", 5)
add("Water Resources", "Arsenic Levels Above Safe Limit in Groundwater", "Lab report from the district health office shows arsenic contamination above the permissible limit in our panchayat's groundwater source.", 6)
add("Water Resources", "Drought Conditions Drying Up Village Pond", "The pond that supplies water for cattle and washing has almost completely dried up due to the extended drought this season.", 7)
add("Water Resources", "Leaking Water Pipeline Wasting Supply for Days", "A major pipeline junction near the primary school has been leaking continuously for a week, and downstream households are getting almost no pressure.", 8)
add("Water Resources", "गंगा जल शुद्धिकरण संयंत्र बंद पड़ा है", "पिछले दो महीने से पानी शुद्ध करने की मशीन खराब पड़ी है, ग्रामीण सीधे नदी का पानी पीने को मजबूर हैं।", 9)
add("Water Resources", "Deep Borewell Needed for Drought-Hit Tribal Hamlet", "Our hamlet has no functioning water source left after the shallow borewell collapsed; we need a deep borewell installed urgently.", 10)
add("Water Resources", "Contaminated Tap Water Causing Stomach Illness", "Several families report diarrhea and stomach illness after the municipal tap water started smelling of sewage last week.", 11)
add("Water Resources", "Broken Water Tank Overflow Flooding Lane", "The overhead water storage tank's valve is stuck open, wasting thousands of litres daily and flooding the adjoining lane.", 12)
add("Water Resources", "kuye ka paani sukh gaya hai is garmi me", "gaon ka purana kuan is baar garmi me sukh gaya, aas paas koi doosra jal srot nahi hai", 13)
add("Water Resources", "Waterlogged Farmland Due to Blocked Drainage Canal", "Excess rainwater has nowhere to drain because the old irrigation canal is blocked, and the standing water is rotting our paddy roots.", 14)
add("Water Resources", "Request for New Borewell Near Anganwadi Centre", "The anganwadi centre and nearby households have no reliable water source; a new borewell close to the centre would serve about 60 families.", 15)
add("Water Resources", "Groundwater Depletion Forcing Long Daily Walks for Water", "The water table in our block has dropped sharply over three summers, and women now spend two hours a day walking to the nearest working source.", 16)
add("Water Resources", "Sewage Mixing Into Drinking Water Line", "A cracked sewage pipe running parallel to the drinking water line has started contaminating supply after the recent road digging work.", 17)

# ---- Agriculture (18) ----
add("Agriculture", "Fall Armyworm Destroying Maize Crop Across Block", "Fall armyworm infestation has spread across nearly 500 acres of maize, and farmers have no access to the recommended pesticide.", 0)
add("Agriculture", "Erratic Monsoon Delaying Paddy Transplantation", "The delayed monsoon has pushed paddy transplantation back by three weeks, threatening yield for over 300 farming households.", 1)
add("Agriculture", "kisano ko sahi beej nahi mil raha hai", "sarkari beej bhandar me is saal accha beej nahi mila, farmer purane stock se kaam chala rahe hain", 2)
add("Agriculture", "No Cold Storage Facility Causing Vegetable Spoilage", "Farmers lose nearly a third of their tomato harvest every season because there is no cold storage facility within 40 km.", 3)
add("Agriculture", "Soil Testing Lab Non-Functional for Six Months", "The block-level soil testing lab has been non-functional for six months, leaving farmers unable to plan fertilizer use accurately.", 4)
add("Agriculture", "फसल बीमा का पैसा अब तक नहीं मिला", "पिछले साल की सूखे से बर्बाद फसल का बीमा क्लेम अभी तक किसानों को नहीं मिला है।", 5)
add("Agriculture", "Livestock Disease Outbreak Killing Village Cattle", "A suspected foot-and-mouth outbreak has already killed several cattle in the village, and no veterinary officer has visited yet.", 6)
add("Agriculture", "Low Mandi Prices Forcing Distress Sale of Paddy", "Farmers are being forced into distress sale of paddy at the mandi far below MSP because there is no procurement centre nearby.", 7)
add("Agriculture", "khet me keede lag gaye hain sabzi kharab ho rahi", "hamari sabzi ki fasal me keede lag gaye hain, pata nahi kaun sa dawai daalna chahiye", 8)
add("Agriculture", "Damaged Irrigation Pump Halting Vegetable Cultivation", "The community irrigation pump that serves vegetable plots has broken down, and repair parts are not locally available.", 9)
add("Agriculture", "Excess Rainfall Waterlogging Paddy Fields", "Continuous heavy rainfall has waterlogged nearly 150 acres of paddy fields, threatening to rot the standing crop.", 10)
add("Agriculture", "Farmers Unable to Access Kisan Credit Card Scheme", "Several tribal farmers report being repeatedly turned away by the bank when applying for the Kisan Credit Card without clear reasons.", 11)
add("Agriculture", "Storage Shed for Harvested Grain Urgently Needed", "Without a proper storage shed, harvested grain kept in the open has been damaged by rats and monsoon dampness two seasons running.", 12)
add("Agriculture", "beej bhandaran ghar nahi hai gaon me", "gaon me anaj rakhne ke liye koi sahi gudam nahi hai, baarish me sab kharab ho jaata hai", 13)
add("Agriculture", "Mango Orchard Affected by Unknown Fungal Disease", "A fungal infection is spreading through the village mango orchard, and no agriculture extension officer has been able to identify it.", 14)
add("Agriculture", "Farmers Seek Drip Irrigation Subsidy Information", "Farmers in our panchayat want to install drip irrigation for vegetable plots but don't know how to apply for the government subsidy.", 15)
add("Agriculture", "Locust-Like Pest Swarm Damaging Standing Crop", "A swarm of crop-eating insects has damaged nearly 40 acres of standing crop overnight, and farmers fear it will spread further.", 16)
add("Agriculture", "No Weighing Scale at Local Procurement Centre", "The government paddy procurement centre has no functioning weighing scale, causing farmers to wait for days or sell elsewhere at a loss.", 17)

# ---- Healthcare (18) ----
add("Healthcare", "No Doctor Available at Night in Primary Health Centre", "The PHC has no doctor present after 6 PM, forcing emergency patients including pregnant women to travel 20 km to the district hospital.", 0)
add("Healthcare", "Ambulance Service Unavailable for Remote Village", "There is no functioning ambulance covering our village, and patients have had to be carried on makeshift stretchers during emergencies.", 1)
add("Healthcare", "aspatal me dawai khatam ho gayi hai", "sarkari aspatal me pichle hafte se zaroori dawaiyan khatam ho gayi hain, mareez bahar se mehngi dawai khareed rahe hain", 2)
add("Healthcare", "High Anemia Rates Among Pregnant Women in Block", "A recent health survey found alarmingly high anemia rates among pregnant women in our block, with limited iron supplementation reaching them.", 3)
add("Healthcare", "Malaria Cases Rising Due to Stagnant Water Near Homes", "Malaria cases have spiked this monsoon because of stagnant water pools near residential areas that have not been fogged or drained.", 4)
add("Healthcare", "गांव में कोई एएनएम नहीं आती नियमित रूप से", "गांव के स्वास्थ्य उपकेंद्र में एएनएम महीनों बाद आती हैं, बच्चों का टीकाकरण समय पर नहीं हो पा रहा।", 5)
add("Healthcare", "Infant Mortality Concerns Due to Lack of Neonatal Care", "Several infant deaths in the last year have been linked to the absence of any neonatal care facility within reasonable distance.", 6)
add("Healthcare", "Sub-Health Centre Building in Dilapidated Condition", "The sub-health centre building has a leaking roof and cracked walls, making it unsafe to use during the monsoon.", 7)
add("Healthcare", "beti ko tez bukhar hai lekin clinic band hai", "hamare gaon ka clinic hafte me sirf do din khulta hai, is waqt sabse najdeek wala band hai", 8)
add("Healthcare", "Vaccination Drive Missed Several Households in Hamlet", "The recent child vaccination drive did not reach several households in our hamlet because the health worker was unaware of the settlement.", 9)
add("Healthcare", "No Blood Bank Access During Obstetric Emergencies", "The nearest blood bank is over 50 km away, and this delay has contributed to at least two maternal near-miss emergencies this year.", 10)
add("Healthcare", "Frequent Waterborne Disease Outbreaks Linked to Contaminated Supply", "Diarrhea and typhoid cases spike every monsoon in our village, which health workers attribute to contaminated drinking water.", 11)
add("Healthcare", "Malnutrition Among Children at Anganwadi Centre", "Growth monitoring at the anganwadi centre shows several children falling into the severely underweight category with no follow-up nutrition plan.", 12)
add("Healthcare", "swasthya kendra me staff ki kami hai", "hamare block ke swasthya kendra me sirf ek nurse hai jo poore ilaake ko sambhalti hai, mareez ghanton intezaar karte hain", 13)
add("Healthcare", "TB Patients Struggling to Access Follow-Up Medication", "Several tuberculosis patients under the DOTS programme have missed follow-up doses because the nearest dispensing centre is inaccessible in monsoon.", 14)
add("Healthcare", "No Disability Screening Camp Held in Two Years", "Persons with disabilities in our panchayat have not had access to a screening or certification camp in over two years, blocking pension access.", 15)
add("Healthcare", "Mobile Medical Unit Stopped Visiting Remote Hamlets", "The mobile medical unit that used to visit our cluster of remote hamlets monthly has not come in the last six months.", 16)
add("Healthcare", "Overcrowded District Hospital Ward Lacking Basic Supplies", "The district hospital's general ward is severely overcrowded and frequently runs out of basic supplies like IV fluids and gloves.", 17)

# ---- Education (18) ----
add("Education", "Government High School Lacks Functional Science Laboratory", "The block's only government high school has a science lab with no working equipment, so students have never done a practical experiment.", 0)
add("Education", "High Dropout Rate Among Tribal Girls After Class 8", "Nearly half the tribal girls in our panchayat drop out after class 8, largely due to distance to the nearest secondary school.", 1)
add("Education", "school me shikshak ki bahut kami hai", "hamare school me sirf do teacher hain paanch class ke liye, bachchon ki padhai bahut prabhavit ho rahi hai", 2)
add("Education", "No Digital Learning Devices Despite Smart Classroom Scheme", "Smart classroom equipment was sanctioned two years ago but never delivered, leaving classrooms without any digital learning tools.", 3)
add("Education", "Midday Meal Quality Complaints From Parents", "Parents have repeatedly complained that the midday meal served at the primary school is insufficient and occasionally spoiled.", 4)
add("Education", "विद्यालय भवन की छत टपक रही है बारिश में", "स्कूल की छत बारिश में टपकती है, बच्चों को क्लास बीच में रोककर घर भेजना पड़ता है।", 5)
add("Education", "Lack of Girls' Toilet Discouraging Secondary Attendance", "The absence of a functional girls' toilet at the secondary school is a major reason cited by parents for daughters dropping out.", 6)
add("Education", "Poor Attendance Due to Long Walking Distance to School", "Children in our remote hamlet walk over 6 km each way to the nearest school, and attendance drops sharply during monsoon.", 7)
add("Education", "bachcho ke paas kitaben nahi hain is saal", "naye session ki kitaben abhi tak nahi bati hain, bachche purani kitaben se kaam chala rahe hain", 8)
add("Education", "No Computer Literacy Training Available for Students", "Despite a computer lab being built two years ago, there has been no functioning internet or trained instructor to teach students.", 9)
add("Education", "Single Teacher Managing Multi-Grade Primary Classroom", "One teacher is responsible for teaching five different grades simultaneously in our primary school, severely affecting learning outcomes.", 10)
add("Education", "Low Literacy Rate Among Adult Women in Panchayat", "Adult literacy classes promised under a state scheme have not started, and most women over 30 in our panchayat remain non-literate.", 11)
add("Education", "Inadequate Furniture Forcing Students to Sit on Floor", "Most students in the upper primary school sit on the floor due to a severe shortage of desks and benches.", 12)
add("Education", "vidyalaya me bijli nahi hai pankha bhi nahi chalta", "garmi me bachche bina pankhe ke padhte hain, school me bijli connection hi nahi hai", 13)
add("Education", "Regional Language Learning Materials Not Distributed", "Textbooks promised in the tribal regional language for early-grade instruction were never distributed to our school this session.", 14)
add("Education", "School Building Shared Unsafely With Livestock Shelter", "During off hours the school compound is used to shelter livestock, and mess left behind creates unhygienic conditions for morning classes.", 15)
add("Education", "No Special Educator for Children With Learning Disabilities", "Several children identified with learning difficulties have no access to a special educator or resource room at the block level.", 16)
add("Education", "Library Books Locked Away and Never Issued to Students", "The school library has a reasonable stock of books, but they remain locked in a cupboard and are never issued to students to read.", 17)

# ---- Sanitation (18) ----
add("Sanitation", "Overflowing Community Toilet Complex Unused for Months", "The community toilet complex built under Swachh Bharat has been overflowing and locked for months due to lack of maintenance.", 0)
add("Sanitation", "Open Garbage Dumping Near Residential Colony", "Garbage from the local market is being dumped in an open plot right next to houses, attracting stray animals and flies.", 1)
add("Sanitation", "safai karamchari kai hafto se nahi aaya", "hamare mohalla me kachra uthane wala kai hafto se nahi aaya, gaali kachre se bhar gayi hai", 2)
add("Sanitation", "Blocked Drainage Causing Sewage to Flow Into Street", "The main drain near the market has been blocked for weeks, and sewage now regularly overflows onto the street during rain.", 3)
add("Sanitation", "No Household Toilets in Newly Settled Tribal Hamlet", "A recently settled tribal hamlet of around 40 households has no toilets at all, and open defecation remains the only option.", 4)
add("Sanitation", "प्लास्टिक कचरे का सही निपटान नहीं हो रहा", "गांव में प्लास्टिक कचरा जलाया जा रहा है क्योंकि कोई उचित निपटान व्यवस्था नहीं है, इससे प्रदूषण बढ़ रहा है।", 5)
add("Sanitation", "Solid Waste Segregation Bins Never Delivered", "Colour-coded waste segregation bins promised under the Swachh Bharat drive were never delivered to our ward.", 6)
add("Sanitation", "Public Toilet Lacking Water Supply Rendered Unusable", "The newly constructed public toilet near the bus stand has no water connection, making it effectively unusable within weeks of opening.", 7)
add("Sanitation", "naali jaam hai machhar bahut badh gaye hain", "gaon ki naali kai mahine se jaam hai, is wajah se machharo ki sankhya bahut badh gayi hai", 8)
add("Sanitation", "Slaughterhouse Waste Dumped Near Drinking Water Source", "Waste from an unregulated local slaughterhouse is being dumped uphill from our drinking water source, raising contamination fears.", 9)
add("Sanitation", "Municipal Waste Truck Skipping Our Ward for Weeks", "The municipal waste collection truck has skipped our ward for nearly three weeks, and garbage is now piling up along the main road.", 10)
add("Sanitation", "No Sanitary Napkin Disposal Facility at Girls' School", "The girls' school has no incinerator or disposal facility for sanitary waste, which is contributing to hygiene and attendance issues.", 11)
add("Sanitation", "Cleanliness Drive Volunteers Report No Support From Panchayat", "A youth group organizing a village cleanliness drive says the panchayat has not provided any tools, bins, or transport support.", 12)
add("Sanitation", "shauchalay ban gaya hai lekin gaddha nahi bhara", "sarkari yojna se shauchalay to ban gaya hai lekin uska soak pit abhi tak nahi bana, istemal nahi ho pa raha", 13)
add("Sanitation", "Drainage Overflow Near Anganwadi During Monsoon", "The open drain next to the anganwadi centre overflows every monsoon, creating unsafe and unhygienic conditions for small children.", 14)
add("Sanitation", "E-Waste and Battery Dumping in Village Common Land", "Discarded electronic waste and old batteries are being dumped on village common land with no safe disposal mechanism in place.", 15)
add("Sanitation", "Public Market Lacks Any Waste Collection Bins", "The weekly haat/market ground has no waste bins at all, leaving vendors to burn or scatter refuse after each market day.", 16)
add("Sanitation", "Community Compost Pit Abandoned Half-Built", "A community compost pit project for organic waste was started but abandoned half-built over a year ago, leaving a hazard pit exposed.", 17)

# ---- Environment (18) ----
add("Environment", "Coal Mine Dust Coating Village Rooftops and Crops", "Fine coal dust from a nearby open-cast mine settles on rooftops, water tanks and standing crops daily, and respiratory complaints are rising.", 0)
add("Environment", "Illegal Deforestation Clearing Community Forest Land", "A contractor has been illegally clearing community forest land bordering our village for the past month with no visible permit.", 1)
add("Environment", "khadaan se dhool aane se saans lene me dikkat", "khadaan ke paas rehne walo ko dhool ki wajah se saans lene me dikkat ho rahi hai, khaaskar bachon aur budhon ko", 2)
add("Environment", "River Turning Black From Untreated Industrial Discharge", "The river running past our village has turned visibly black and foul-smelling, which locals attribute to untreated factory discharge upstream.", 3)
add("Environment", "Air Quality Worsening Near Cement Factory", "Residents near the cement factory report worsening air quality, with fine dust settling on clothes and vegetation daily.", 4)
add("Environment", "जंगल में आग बार बार लग रही है इस मौसम में", "पिछले एक महीने में जंगल में तीन बार आग लग चुकी है, वन विभाग की कोई कार्रवाई नहीं हुई।", 5)
add("Environment", "Mining Blasting Cracking Nearby House Walls", "Repeated blasting at the nearby mine has caused visible cracks in the walls of several houses in the adjoining hamlet.", 6)
add("Environment", "Wildlife Straying Into Fields Due to Habitat Loss", "Elephants have been straying into farmland more frequently this year, which villagers link to shrinking forest cover nearby.", 7)
add("Environment", "khadaan ke gaddhe me paani bhar gaya bachche gir sakte", "purani band khadaan ke gaddhe me barish ka paani bhar gaya hai, koi baada nahi hai, bachcho ke liye khatra hai", 8)
add("Environment", "Unregulated Stone Crusher Polluting Nearby Fields", "A stone crusher unit operating without proper dust control has been coating nearby agricultural fields in fine particulate for months.", 9)
add("Environment", "Smog Reducing Visibility Near Industrial Cluster", "Thick smog from the nearby industrial cluster reduces visibility on the approach road most mornings during winter, raising accident risk.", 10)
add("Environment", "Coal Slurry Overflow Contaminating Farmland After Rain", "Coal slurry from a mining pond overflowed after heavy rain and contaminated nearly 30 acres of adjoining farmland.", 11)
add("Environment", "Tree Felling for Road Widening Without Compensatory Plantation", "Dozens of old trees were felled for a road widening project with no visible compensatory plantation drive as promised.", 12)
add("Environment", "vaayu pradushan se bachcho ko khaansi ho rahi hai", "khadaan ilaake ke bachcho ko lagatar khaansi aur saans ki problem ho rahi hai, jaanch karayi jaaye", 13)
add("Environment", "Illegal Sand Mining Eroding Riverbank Near Village", "Unregulated sand mining on the riverbank near our village is causing visible erosion and threatens the approach road during monsoon.", 14)
add("Environment", "Toxic Fumes From Brick Kiln Affecting Nearby Homes", "A brick kiln operating close to residential homes releases thick smoke daily, and several families report persistent eye irritation.", 15)
add("Environment", "Declining Groundwater Recharge Linked to Deforestation", "Villagers link the steadily declining groundwater recharge over the past decade to large-scale deforestation on the surrounding hills.", 16)
add("Environment", "Chemical Foam Forming in Village Pond After Factory Runoff", "Thick chemical foam has been appearing on the village pond surface after monsoon runoff from a nearby factory drain.", 17)

# ---- Energy (18) ----
add("Energy", "Transformer Burnt Out Leaving Hamlet Without Power", "The single transformer serving our hamlet burnt out three weeks ago and has not been replaced, leaving 60 households without electricity.", 0)
add("Energy", "18-Hour Load Shedding Disrupting Evening Study and Irrigation", "Daily load shedding of up to 18 hours is severely affecting children's evening study time and irrigation pump operation.", 1)
add("Energy", "bijli ka khambha gir gaya sadak par", "toofaan me bijli ka khambha sadak par gir gaya hai, tar khule pade hain, koi durghatna ho sakti hai", 2)
add("Energy", "Voltage Fluctuation Damaging Household Appliances", "Severe voltage fluctuation over the past month has already damaged several households' refrigerators and water pumps.", 3)
add("Energy", "Solar Streetlights Installed but Never Functional", "Solar streetlights installed along the main village road two years ago have never worked due to faulty batteries that were never replaced.", 4)
add("Energy", "बिजली बिल बहुत ज़्यादा आ रहा है बिना खपत के", "पिछले तीन महीने से बिजली का बिल असामान्य रूप से ज्यादा आ रहा है जबकि खपत वैसी ही है।", 5)
add("Energy", "Frequent Blackouts During Exam Season Affecting Students", "Frequent unscheduled blackouts during the ongoing exam season are seriously affecting students preparing for board exams.", 6)
add("Energy", "No Electricity Connection Despite Saubhagya Scheme Enrollment", "Our household was enrolled under the Saubhagya electrification scheme over a year ago but still has no working connection.", 7)
add("Energy", "khamba bahut door hai naye ghar tak connection nahi", "naye basaye gaye ghar tak bijli ka khamba bahut door hai, connection lene ke liye alag se paisa maanga ja raha hai", 8)
add("Energy", "Biogas Plant Sanctioned Two Years Ago Still Not Built", "A community biogas plant sanctioned two years ago under a rural energy scheme has still not been constructed despite funds being released.", 9)
add("Energy", "Overloaded Grid Causing Repeated Tripping in Summer", "The local grid trips repeatedly every afternoon in summer due to overload, cutting power just when irrigation pumps are needed most.", 10)
add("Energy", "Damaged Power Lines Hanging Low Over Village Road", "Storm-damaged power lines are hanging dangerously low over the main village road, posing a serious safety risk to passersby.", 11)
add("Energy", "Renewable Micro-Grid Project Stalled Midway", "A sanctioned solar micro-grid project for our unelectrified cluster has been stalled midway for over a year with no clear timeline.", 12)
add("Energy", "inverter aur battery ka koi intezaam nahi hai school me", "school me computer lab ke liye bijli nahi rehti, na hi koi inverter battery ka backup hai", 13)
add("Energy", "Streetlight Poles Without Bulbs for Over a Year", "Most streetlight poles installed along our village road have had no functioning bulbs for over a year, making night travel unsafe.", 14)
add("Energy", "Illegal Power Tapping Causing Repeated Local Outages", "Illegal tapping of the main power line by a few households is causing repeated voltage drops and outages for the rest of the hamlet.", 15)
add("Energy", "Diesel Generator Costs Burdening Local Shopkeepers", "With power cuts lasting most of the day, local shopkeepers are spending heavily on diesel generators just to stay open.", 16)
add("Energy", "New Transformer Capacity Insufficient for Growing Hamlet", "The transformer installed for our hamlet years ago is undersized for the number of households that have since been added, causing frequent trips.", 17)

# ---- Urban Infrastructure (18) ----
add("Urban Infrastructure", "Collapsed Bridge Pier Cutting Off Village Access Road", "A support pier on the bridge connecting our village to the main road has cracked and partially collapsed, cutting off safe vehicle access.", 0)
add("Urban Infrastructure", "Deep Potholes Causing Accidents on Main Village Road", "Deep, unrepaired potholes on the main village road have caused several two-wheeler accidents in the past two months.", 1)
add("Urban Infrastructure", "sadak bahut kharab hai gaddo se bhari", "gaon ki sadak me itne gaddhe hain ki gaadi chalana mushkil ho gaya hai, khaaskar raat me durghatna ka khatra hai", 2)
add("Urban Infrastructure", "No Street Lighting on Stretch Near School", "The stretch of road between the bus stop and the school has no street lighting, making it unsafe for children walking home in winter evenings.", 3)
add("Urban Infrastructure", "Overflowing Storm Drain Flooding Main Bazaar Road", "The storm drain along the main bazaar road overflows with every heavy rain, flooding shops and blocking traffic for hours.", 4)
add("Urban Infrastructure", "पुल का हैंडरेल टूटा हुआ है खतरनाक स्थिति में", "गांव के छोटे पुल का रेलिंग कई जगह से टूट गया है, बच्चों के लिए बहुत खतरनाक है।", 5)
add("Urban Infrastructure", "No Bus Stop Shelter Leaving Commuters Exposed to Rain", "Daily commuters including schoolchildren have no shelter at the bus stop and are left exposed to heavy monsoon rain every day.", 6)
add("Urban Infrastructure", "Narrow Village Road Blocking Ambulance Access", "The approach road to our hamlet is too narrow for an ambulance to pass, which delayed emergency transport during a recent medical crisis.", 7)
add("Urban Infrastructure", "pull ka nirmaan kaam adhoora chhoda gaya", "kai mahine pehle shuru hua pul ka nirmaan kaam beech me hi chhod diya gaya hai, log ab bhi ghoom kar jaate hain", 8)
add("Urban Infrastructure", "Traffic Congestion Near Weekly Market Causing Delays", "Severe traffic congestion builds up near the weekly market ground due to the absence of proper parking or traffic management.", 9)
add("Urban Infrastructure", "Flyover Construction Debris Left Blocking Footpath", "Construction debris from the ongoing flyover project has been left blocking the pedestrian footpath for over two months.", 10)
add("Urban Infrastructure", "Culvert Washed Away Cutting Off Two Hamlets", "A small culvert connecting two hamlets was washed away in last monsoon's flooding and has not been rebuilt since.", 11)
add("Urban Infrastructure", "Unpaved Road Turning to Mud Every Monsoon", "The road leading to our hamlet remains unpaved and turns into thick mud every monsoon, cutting off vehicle access for weeks.", 12)
add("Urban Infrastructure", "sadak ke kinare koi footpath nahi hai school ke bachcho ke liye", "school jaane wale bachcho ke liye sadak par koi alag footpath nahi hai, gaadiyon ke beech chalna padta hai", 13)
add("Urban Infrastructure", "Damaged Guard Rail on Hillside Village Road", "The guard rail along a sharp hillside curve on the village access road has been damaged for months, raising serious accident risk.", 14)
add("Urban Infrastructure", "Public Parking Encroached by Illegal Vendors", "The designated public parking area near the block office has been almost entirely encroached upon by illegal roadside vendors.", 15)
add("Urban Infrastructure", "Railway Level Crossing Gate Frequently Malfunctioning", "The manual level crossing gate on the road to our village frequently malfunctions, occasionally staying open during train passage.", 16)
add("Urban Infrastructure", "No Footbridge Over Seasonal Stream Cutting Off School Route", "Children have to wade through a seasonal stream to reach school every monsoon because there is no footbridge along the route.", 17)

# ---- Rural Livelihoods (18) ----
add("Rural Livelihoods", "Tribal Artisans Unable to Sell Handicrafts Beyond Local Haat", "Skilled bamboo and cane artisans in our village have no market access beyond the local weekly haat and are forced to sell at very low prices.", 0)
add("Rural Livelihoods", "Self Help Group Unable to Access Promised Bank Loan", "A women's self help group that completed all required training has been waiting over six months for the promised bank loan to start their venture.", 1)
add("Rural Livelihoods", "gaon me rozgaar ka koi sadhan nahi bacha", "MGNREGA ka kaam bhi is saal bahut kam mila hai, log kaam ki talaash me shehar ja rahe hain", 2)
add("Rural Livelihoods", "Lac Cultivation Income Falling Due to Lack of Processing Unit", "Tribal families dependent on lac cultivation are earning far less because there is no local processing unit, forcing sale of raw lac at low prices.", 3)
add("Rural Livelihoods", "Tussar Silk Weavers Struggling With Outdated Looms", "Tussar silk weavers in our cluster are still using decades-old looms, drastically limiting output compared to mechanized units elsewhere.", 4)
add("Rural Livelihoods", "स्वयं सहायता समूह को प्रशिक्षण के बाद भी काम नहीं मिला", "महिला स्वयं सहायता समूह ने सिलाई प्रशिक्षण पूरा कर लिया लेकिन उन्हें अब तक कोई ऑर्डर या बाज़ार नहीं मिला।", 5)
add("Rural Livelihoods", "Forest Produce Collectors Facing Middleman Exploitation", "Mahua and tendu leaf collectors in our village say middlemen are paying far below fair rates with no alternative direct-sale channel.", 6)
add("Rural Livelihoods", "MGNREGA Wages Delayed for Over Two Months", "Workers who completed MGNREGA work in our panchayat have not received wages for over two months despite repeated follow-up.", 7)
add("Rural Livelihoods", "haathkargha kaarigaro ko raw material nahi mil raha", "bunkaro ko dhaage aur rang samay par nahi milte, isse unka utpaadan bahut kam ho gaya hai", 8)
add("Rural Livelihoods", "No Cold Chain for Dairy Farmers Losing Milk to Spoilage", "Small dairy farmers in our cluster lose a significant share of milk to spoilage daily because there is no cold chain or nearby collection centre.", 9)
add("Rural Livelihoods", "Youth Migration Rising Due to Lack of Local Employment", "A growing number of young people are migrating to cities for daily wage work because there are almost no local livelihood opportunities.", 10)
add("Rural Livelihoods", "Bamboo Craft Cluster Lacking Quality Certification Support", "Our bamboo craft cluster produces good quality goods but has no support to get quality certification needed for larger retail orders.", 11)
add("Rural Livelihoods", "Poultry Farming SHG Struggling Without Veterinary Support", "A women-led poultry farming self help group has lost several batches of birds to disease due to lack of nearby veterinary support.", 12)
add("Rural Livelihoods", "gaon ki mahilao ko sahi daam nahi mil rahe apne saaman ka", "SHG ki mahilaayen achhe utpaad banati hain lekin unhe bazaar tak pahunchne ka koi sahi raasta nahi hai", 13)
add("Rural Livelihoods", "No QR-Based Traceability for Fair-Trade Tribal Crafts", "Tribal craft buyers increasingly want traceability information, but our artisan cooperative has no digital system to provide it.", 14)
add("Rural Livelihoods", "Handloom Cooperative Struggling to Repay Working Capital Loan", "The village handloom cooperative is struggling to repay its working capital loan because seasonal demand has dropped sharply this year.", 15)
add("Rural Livelihoods", "Seasonal Migration Leaving Children Without Adult Supervision", "Large-scale seasonal migration for brick-kiln work leaves many children in the village without adult supervision for months at a time.", 16)
add("Rural Livelihoods", "Fisherfolk Community Lacking Access to Cold Storage Boats", "Small-scale fisherfolk on the reservoir lose a large share of catch value due to lack of ice or cold storage during transport to market.", 17)

# ---- Accessibility (18) ----
add("Accessibility", "No Wheelchair Ramp at Primary Health Centre Entrance", "The primary health centre has a steep entrance staircase with no ramp, making it inaccessible for wheelchair users and elderly patients.", 0)
add("Accessibility", "Blind Villager Struggling Without Braille Signage Anywhere", "A visually impaired resident reports that no government building in the block, including the panchayat office, has any braille signage.", 1)
add("Accessibility", "viklang vyakti ko pension milne me bahut dikkat ho rahi", "hamare gaon ke divyang vyakti ko pension form bharne ke liye baar baar block office jaana padta hai jo bahut door hai", 2)
add("Accessibility", "School Has No Accessible Toilet for Disabled Students", "The only toilet at the block school is up a flight of stairs, leaving the two wheelchair-using students unable to use it independently.", 3)
add("Accessibility", "Hearing-Impaired Students Lack Sign Language Support at School", "Two hearing-impaired children enrolled in our village school have no sign language interpreter or trained special educator available.", 4)
add("Accessibility", "दिव्यांग बच्चों के लिए स्कूल में कोई सुविधा नहीं है", "गांव के स्कूल में दिव्यांग बच्चों के लिए न कोई रैंप है और न ही कोई विशेष शिक्षक।", 5)
add("Accessibility", "No Accessible Public Transport for Disabled Villagers", "There is no accessible public transport option for wheelchair users in our block, forcing families to arrange costly private transport.", 6)
add("Accessibility", "Community Hall Steps Blocking Access for Elderly and Disabled", "The steep steps at the newly built community hall entrance make it impossible for elderly residents and wheelchair users to attend meetings.", 7)
add("Accessibility", "divyang praman patra banwane me bahut samay lag raha hai", "hamare gaon ke ek vyakti ko divyang certificate banwane me 6 mahine se zyada ho gaye, baar baar chakkar lagwaya ja raha hai", 8)
add("Accessibility", "No Assistive Devices Distributed Despite Camp Promises", "A disability assessment camp identified over 20 people needing wheelchairs or hearing aids a year ago, but no devices have been distributed since.", 9)
add("Accessibility", "Panchayat Office Entrance Inaccessible to Wheelchair Users", "The panchayat office has a raised entrance with no ramp, so wheelchair-using residents cannot independently access grievance services.", 10)
add("Accessibility", "Visually Impaired Farmer Needs Voice-Guided Navigation Support", "A visually impaired farmer in our village struggles to navigate to the market and health centre alone due to lack of any assistive tools.", 11)
add("Accessibility", "Anganwadi Centre Not Accessible for Disabled Toddlers", "The anganwadi centre building has a high threshold step that prevents a disabled toddler in a mobility aid from being brought inside easily.", 12)
add("Accessibility", "sunne me dikkat wale bacho ke liye koi madad nahi", "hamare gaon me do bacche kam sunte hain, unke liye school me koi khaas suvidha nahi hai", 13)
add("Accessibility", "Railway Station Lacks Any Accessibility Features for Disabled", "The nearest railway station has no ramps, tactile paths, or accessible toilets, making travel extremely difficult for disabled passengers.", 14)
add("Accessibility", "Water Handpump Platform Not Usable by Wheelchair Users", "The raised platform around the community handpump makes it impossible for a wheelchair-using resident to draw water without assistance.", 15)
add("Accessibility", "No Accessible Voting Booth During Panchayat Elections", "During the last panchayat election, the voting booth had steps with no ramp, forcing elderly and disabled voters to be carried inside.", 16)
add("Accessibility", "Deaf Villager Unable to Access Grievance Redressal Help Desk", "A deaf resident says the block's grievance redressal help desk has no provision for sign language or written communication support.", 17)

# ---- Public Administration (18) ----
add("Public Administration", "Pension Payments Delayed for Elderly Villagers for Months", "Old-age pension payments for over 40 elderly residents in our panchayat have been delayed for the past three months with no explanation.", 0)
add("Public Administration", "Ration Card Applications Stuck for Over a Year", "Several families who applied for new ration cards over a year ago have received no update despite repeated visits to the block office.", 1)
add("Public Administration", "aadhar card me galti sudharne me bahut samay lag raha hai", "hamare gaon ke kai logo ka aadhar card me naam galat hai, sudharne ke liye baar baar center jaana pad raha hai bina kisi nateeje ke", 2)
add("Public Administration", "DBT Transfers Not Reaching Bank Accounts of Beneficiaries", "Direct benefit transfer payments under a state scheme have not been credited to several beneficiaries' bank accounts for two cycles.", 3)
add("Public Administration", "Grievance Filed at Panchayat Office Never Acknowledged", "A written grievance about a broken handpump was submitted to the panchayat office two months ago and has never been acknowledged.", 4)
add("Public Administration", "जन्म प्रमाण पत्र बनवाने में महीनों लग रहे हैं", "बच्चे का जन्म प्रमाण पत्र बनवाने के लिए तीन महीने से ब्लॉक कार्यालय के चक्कर लगा रहे हैं, कोई जवाब नहीं मिल रहा।", 5)
add("Public Administration", "Corruption Alleged in Ration Shop Weighment Practices", "Villagers allege the local fair price shop consistently under-weighs ration grain, and complaints to the block office have gone unanswered.", 6)
add("Public Administration", "Caste Certificate Application Pending Without Reason for Months", "A student's caste certificate application, needed urgently for a scholarship deadline, has been pending for four months with no stated reason.", 7)
add("Public Administration", "MGNREGA job card banwane me rishwat maangi ja rahi hai", "gaon walo ka aarop hai ki job card banwane ke liye bina paisa diye kaam nahi hota, is baare me shikayat karni hai", 8)
add("Public Administration", "Panchayat Records Missing for Recently Constructed Assets", "Villagers cannot get information on funds spent on a recently constructed community asset because panchayat records are reportedly missing.", 9)
add("Public Administration", "Widow Pension Application Rejected Without Clear Reason", "A widow's pension application was rejected without any written reason provided, and she has been unable to get clarity despite several visits.", 10)
add("Public Administration", "Service Delivery Counter Frequently Closed During Working Hours", "The block-level service delivery counter for certificates and DBT queries is frequently closed during its stated working hours.", 11)
add("Public Administration", "Land Record Mutation Stuck Due to Alleged Bureaucratic Delay", "A land mutation request following inheritance has been stuck for over a year, and the family suspects it is being deliberately delayed.", 12)
add("Public Administration", "panchayat se milne wali suvidha ki jaankari nahi milti", "gaon walo ko yeh pata nahi chalta ki kaun si sarkari yojna unke liye hai aur uska form kaise bhara jaata hai", 13)
add("Public Administration", "Old-Age Home Verification Visit Never Conducted Despite Application", "An elderly applicant for an old-age support scheme says the mandatory verification visit was never conducted despite the application being submitted months ago.", 14)
add("Public Administration", "Disability Pension File Reportedly Lost at Block Office", "A disabled applicant's pension file has reportedly gone missing at the block office, and staff have been unable to trace it for weeks.", 15)
add("Public Administration", "RTI Application on Panchayat Spending Ignored Past Deadline", "An RTI application seeking details of panchayat fund utilization was filed well past the statutory reply deadline with no response.", 16)
add("Public Administration", "Grievance Redressal Helpline Never Answers Calls", "The district grievance redressal helpline number listed on official posters rings unanswered on every attempt over the past two weeks.", 17)


TOTAL_EXPECTED = 11 * 18  # 198
TEST_SAMPLES = SAMPLES

# The deployed default: keywords only (AI_EMBEDDINGS_ENABLED is off by default).
# Pinned here so enabling embeddings locally cannot change the headline figure.
RELEASED = AIClassificationService(embeddings=False)

ABLATIONS = [
    ("a. expanded multilingual lexicon, uniform weights",
     dict(weighted=False, negation=False, tie_break=False, embeddings=False)),
    ("b. + weighted phrases and title boost",
     dict(weighted=True, negation=False, tie_break=False, embeddings=False)),
    ("c. + topic-negation handling",
     dict(weighted=True, negation=True, tie_break=False, embeddings=False)),
    ("d. + runner-up margin tie-break (released, keywords-only)",
     dict(weighted=True, negation=True, tie_break=True, embeddings=False)),
]


def fingerprint_test_set(samples=SAMPLES) -> str:
    canonical = json.dumps(
        [[s["true_domain"], s["title"], s["description"]] for s in samples], ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_train_dev():
    """Returns (train, dev): every DEV_EVERY-th report per domain is DEV."""
    train, dev = [], []
    position = Counter()
    for line in TRAIN_DEV_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        item = {
            "title": row["title"],
            "description": row["description"],
            "true_domain": row["domain"],
            "lang": row["lang"],
        }
        is_dev = position[row["domain"]] % DEV_EVERY == DEV_EVERY - 1
        (dev if is_dev else train).append(item)
        position[row["domain"]] += 1
    return train, dev


def _predict(samples, classifier):
    for item in samples:
        out = classifier.classify(title=item["title"], description=item["description"]).output
        yield item, out


def evaluate(samples, classifier=RELEASED) -> dict:
    per_total, per_correct = Counter(), Counter()
    lang_total, lang_correct = Counter(), Counter()
    confusion = defaultdict(Counter)
    flagged = flagged_correct = 0
    misclassified = []

    for item, out in _predict(samples, classifier):
        pred, true = out["domain"], item["true_domain"]
        ok = pred == true
        per_total[true] += 1
        per_correct[true] += ok
        confusion[true][pred] += 1
        if "lang" in item:
            lang_total[item["lang"]] += 1
            lang_correct[item["lang"]] += ok
        if out["requires_human_review"]:
            flagged += 1
            flagged_correct += ok
        if not ok:
            misclassified.append({
                "title": item["title"],
                "true_domain": true,
                "predicted_domain": pred,
                "runner_up_domain": out.get("runner_up_domain"),
                "confidence": out.get("confidence"),
                "requires_human_review": out["requires_human_review"],
                "matched_keywords": out.get("matched_keywords", []),
            })

    total = len(samples)
    correct = sum(per_correct.values())
    auto = total - flagged
    result = {
        "total_samples": total,
        "correct": correct,
        "accuracy": round(correct / total, 4),
        "accuracy_pct": f"{correct / total * 100:.1f}%",
        "human_review_flagged": flagged,
        "auto_accepted_accuracy": round((correct - flagged_correct) / auto, 4) if auto else None,
        "flagged_accuracy": round(flagged_correct / flagged, 4) if flagged else None,
        "per_domain": {
            dom: {
                "n": per_total[dom],
                "correct": per_correct[dom],
                "accuracy": round(per_correct[dom] / per_total[dom], 3),
            }
            for dom in sorted(per_total)
        },
        "confusion_matrix": {t: dict(v) for t, v in sorted(confusion.items())},
        "misclassified_examples": misclassified,
    }
    if lang_total:
        result["per_language"] = {
            lang: {"n": lang_total[lang], "accuracy": round(lang_correct[lang] / lang_total[lang], 3)}
            for lang in sorted(lang_total)
        }
    return result


def load_v2_module():
    """The classifier module at V2_REFERENCE_COMMIT, loaded from git history for comparison."""
    try:
        source = subprocess.run(
            ["git", "show", f"{V2_REFERENCE_COMMIT}:backend/app/services/ai/classification_service.py"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    module = types.ModuleType("classification_service_v2")
    exec(compile(source, "classification_service_v2.py", "exec"), module.__dict__)
    return module


def _lexicon_hits(samples) -> set:
    hits = set()
    for s in samples:
        text = _normalise(f"{s['title']} . {s['description']}")
        for domain, term, _weight, pattern in _COMPILED_LEXICON:
            if pattern.search(text):
                hits.add((domain, term))
    return hits


def audit_test_only_terms(train, dev, v2_module) -> list:
    """
    Leakage audit: lexicon entries that fire on some TEST report but on no
    TRAIN/DEV report and were not already in the V2 taxonomy. These are the
    terms most likely to have been added after reading the TEST set.
    """
    v2_terms = set()
    if v2_module is not None:
        v2_terms = {t for terms in v2_module.CONTROLLED_TAXONOMY.values() for t in terms}
    candidates = _lexicon_hits(SAMPLES) - _lexicon_hits(train + dev)
    return sorted((d, t) for d, t in candidates if t.rstrip("*") not in v2_terms)


def calibrate(dev) -> None:
    """Prints DEV-only accuracy above/below candidate review thresholds."""
    rows = [(out["confidence"], out["domain"] == item["true_domain"])
            for item, out in _predict(dev, RELEASED)]
    print(f"Review-threshold calibration on DEV ({len(rows)} items)")
    print(f"{'threshold':>10}{'flagged':>10}{'auto acc':>10}{'flagged acc':>13}")
    for step in range(8, 17):
        t = step * 0.05
        auto = [ok for conf, ok in rows if conf >= t]
        low = [ok for conf, ok in rows if conf < t]
        auto_acc = f"{sum(auto) / len(auto) * 100:.1f}%" if auto else "-"
        low_acc = f"{sum(low) / len(low) * 100:.1f}%" if low else "-"
        print(f"{t:>10.2f}{len(low):>10}{auto_acc:>10}{low_acc:>13}")


def _summary(result: dict) -> dict:
    keep = ("total_samples", "correct", "accuracy", "accuracy_pct", "human_review_flagged",
            "auto_accepted_accuracy", "flagged_accuracy", "per_domain", "per_language")
    return {k: result[k] for k in keep if k in result}


def _print_domain_table(dev: dict, test: dict) -> None:
    print(f"{'Domain':<24}{'DEV':>12}{'TEST':>12}")
    for dom in test["per_domain"]:
        d, t = dev["per_domain"][dom], test["per_domain"][dom]
        print(f"{dom:<24}{d['correct']:>4}/{d['n']:<3}{d['accuracy'] * 100:>4.0f}%"
              f"{t['correct']:>4}/{t['n']:<3}{t['accuracy'] * 100:>4.0f}%")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--calibrate", action="store_true", help="print DEV review-threshold table and exit")
    parser.add_argument("--no-write", action="store_true", help="do not rewrite ai_accuracy_report.json")
    args = parser.parse_args()

    assert len(SAMPLES) == TOTAL_EXPECTED, f"Expected {TOTAL_EXPECTED} samples, got {len(SAMPLES)}"
    train, dev = load_train_dev()
    if args.calibrate:
        calibrate(dev)
        return

    results = {name: evaluate(split) for name, split in (("train", train), ("dev", dev), ("test", SAMPLES))}
    test = results["test"]

    ablation = []
    variants = list(ABLATIONS)
    if embedding_service.is_available():
        variants.append(("e. + 0.6/0.4 sentence-embedding blend",
                         dict(weighted=True, negation=True, tie_break=True, embeddings=True)))
    v2_module = load_v2_module()
    if v2_module is not None:
        v2 = v2_module.AIClassificationService()
        ablation.append({
            "variant": f"V2 keyword counter (commit {V2_REFERENCE_COMMIT})",
            "dev_accuracy": evaluate(dev, v2)["accuracy"],
            "test_accuracy": evaluate(SAMPLES, v2)["accuracy"],
        })
    for label, options in variants:
        variant = AIClassificationService(**options)
        ablation.append({
            "variant": label,
            "dev_accuracy": evaluate(dev, variant)["accuracy"],
            "test_accuracy": evaluate(SAMPLES, variant)["accuracy"],
        })

    audit_terms = audit_test_only_terms(train, dev, v2_module)
    audited = evaluate(SAMPLES, AIClassificationService(embeddings=False, exclude_terms=set(audit_terms)))

    report = {
        "model_name": RELEASED.MODEL_NAME,
        "model_version": RELEASED.MODEL_VERSION,
        "method": "keywords",
        "review_threshold": REVIEW_CONFIDENCE_THRESHOLD,
        "splits": {
            "test": f"{len(SAMPLES)} held-out reports in scripts/ai_accuracy_benchmark.py (never used for tuning)",
            "train": f"{len(train)} reports from scripts/ai_eval/train_dev.jsonl",
            "dev": f"{len(dev)} reports from scripts/ai_eval/train_dev.jsonl (every {DEV_EVERY}th per domain)",
        },
        "test_set_sha256": fingerprint_test_set(),
        **test,
        "dev": {**_summary(results["dev"]), "misclassified_examples": results["dev"]["misclassified_examples"]},
        "train": _summary(results["train"]),
        "ablation": ablation,
        "embedding_model": settings.AI_EMBEDDINGS_MODEL_NAME if embedding_service.is_available() else None,
        "leakage_audit": {
            "description": "Released classifier re-run on TEST with every lexicon term removed that "
                           "fires only on TEST reports and was not in the V2 taxonomy.",
            "terms_removed": [f"{d}: {t}" for d, t in audit_terms],
            "test_accuracy": audited["accuracy"],
            "per_domain": {d: v["accuracy"] for d, v in audited["per_domain"].items()},
        },
    }

    if not args.no_write:
        with open("ai_accuracy_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print(f"Model: {report['model_name']} v{report['model_version']} ({report['method']})")
    for name in ("train", "dev", "test"):
        r = results[name]
        print(f"{name.upper():<6} n={r['total_samples']:<4} accuracy {r['accuracy_pct']:>6}  "
              f"flagged for review {r['human_review_flagged']:>3}  "
              f"auto-accepted accuracy {(r['auto_accepted_accuracy'] or 0) * 100:.1f}%")
    print()
    _print_domain_table(results["dev"], test)
    print()
    print("Ablation (accuracy):")
    for row in ablation:
        print(f"  {row['variant']:<62} DEV {row['dev_accuracy'] * 100:5.1f}%  TEST {row['test_accuracy'] * 100:5.1f}%")
    print(f"Leakage audit: {len(audit_terms)} TEST-only terms removed -> TEST {audited['accuracy_pct']}")
    if not args.no_write:
        print()
        print("Full report written to ai_accuracy_report.json")


if __name__ == "__main__":
    main()
