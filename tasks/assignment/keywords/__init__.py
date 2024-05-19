import tasks.assignment.keywords.entry as KEYWORDS_ASSIGNMENT_ENTRY
import tasks.assignment.keywords.entry_detailed as KEYWORDS_ASSIGNMENT_ENTRY_DETAILED
import tasks.assignment.keywords.group as KEYWORDS_ASSIGNMENT_GROUP
import tasks.assignment.keywords.event_entry as KEYWORDS_ASSIGNMENT_EVENT_ENTRY
import tasks.assignment.keywords.event_group as KEYWORDS_ASSIGNMENT_EVENT_GROUP
from tasks.assignment.keywords.classes import *

KEYWORDS_ASSIGNMENT_GROUP.Character_Materials.entries = (
    KEYWORDS_ASSIGNMENT_ENTRY.Nine_Billion_Names,
    KEYWORDS_ASSIGNMENT_ENTRY.Destruction_of_the_Destroyer,
    KEYWORDS_ASSIGNMENT_ENTRY.Winter_Soldiers,
    KEYWORDS_ASSIGNMENT_ENTRY.Born_to_Obey,
    KEYWORDS_ASSIGNMENT_ENTRY.Root_Out_the_Turpitude,
    KEYWORDS_ASSIGNMENT_ENTRY.Fire_Lord_Inflames_Blades_of_War,
    KEYWORDS_ASSIGNMENT_ENTRY.A_Startling_Night_Terror,
    KEYWORDS_ASSIGNMENT_ENTRY.Tranquility_of_Vimala_bhumi,
)
KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits.entries = (
    KEYWORDS_ASSIGNMENT_ENTRY.Nameless_Land_Nameless_People,
    KEYWORDS_ASSIGNMENT_ENTRY.Akashic_Records,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Invisible_Hand,
)
KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials.entries = (
    KEYWORDS_ASSIGNMENT_ENTRY.Abandoned_and_Insulted,
    KEYWORDS_ASSIGNMENT_ENTRY.Spring_of_Life,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Land_of_Gold,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Blossom_in_the_Storm,
    KEYWORDS_ASSIGNMENT_ENTRY.Legend_of_the_Puppet_Master,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Wages_of_Humanity,
    KEYWORDS_ASSIGNMENT_ENTRY.Fragments_of_Illusory_Dreams,
    KEYWORDS_ASSIGNMENT_ENTRY.Scalpel_and_Screwdriver,
)
KEYWORDS_ASSIGNMENT_EVENT_GROUP.All_About_Boothill.entries = (
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Activate_Genetic_Samples,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Reproduce_Experimental_Data,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Burned_Warehouse,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Car_Thief,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Synesthesia_Beacon_Function_Iteration,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Hunters_Wanted_No_Newbies_Please,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Peaceful_Life_for_Good_People,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Closed_Beta_Test_Recruitment,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Protect_Digital_Exhibits,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Final_Survivor,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Water_Pollution_Control,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Hook_Line_and_Sinker,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Investigation_Order_Boothill,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Volunteers_Wanted,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Burn_Treatment,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.I_Want_to_Speak_to_Your_Manager,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Licensed_Product_Damage_Assessment,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Annoying_Flies,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Urgent_Protection_Services,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.A_Dream_Is_Born,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Wanted_Boothill,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Casual_Cowboy,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Dangerous_Journey,
    KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Crossing_the_Fire_Line,
)
for group in (
        KEYWORDS_ASSIGNMENT_GROUP.Character_Materials,
        KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits,
        KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials,
        KEYWORDS_ASSIGNMENT_EVENT_GROUP.All_About_Boothill,
):
    for entry in group.entries:
        assert entry.group is None
        entry.group = group
