import tasks.assignment.keywords.entry as KEYWORDS_ASSIGNMENT_ENTRY
import tasks.assignment.keywords.entry_detailed as KEYWORDS_ASSIGNMENT_ENTRY_DETAILED
import tasks.assignment.keywords.group as KEYWORDS_ASSIGNMENT_GROUP
import tasks.assignment.keywords.event_entry as KEYWORDS_ASSIGNMENT_EVENT_ENTRY
import tasks.assignment.keywords.event_group as KEYWORDS_ASSIGNMENT_EVENT_GROUP
from tasks.assignment.keywords.classes import *

CURRENT_EVENT_GROUP = KEYWORDS_ASSIGNMENT_EVENT_GROUP.Shadow_of_the_Ranger
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
    KEYWORDS_ASSIGNMENT_ENTRY.Scalpel_and_Screwdriver,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Wages_of_Humanity,
    KEYWORDS_ASSIGNMENT_ENTRY.Legend_of_the_Puppet_Master,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Land_of_Gold,
    KEYWORDS_ASSIGNMENT_ENTRY.Spring_of_Life,
    KEYWORDS_ASSIGNMENT_ENTRY.Fragments_of_Illusory_Dreams,
    KEYWORDS_ASSIGNMENT_ENTRY.The_Blossom_in_the_Storm,
    KEYWORDS_ASSIGNMENT_ENTRY.Abandoned_and_Insulted,
    KEYWORDS_ASSIGNMENT_ENTRY.Record_of_Expeditions,
    KEYWORDS_ASSIGNMENT_ENTRY.Work_and_Days,
)
CURRENT_EVENT_GROUP.entries = tuple(AssignmentEventEntry.instances.values())
for group in (
        KEYWORDS_ASSIGNMENT_GROUP.Character_Materials,
        KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits,
        KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials,
        CURRENT_EVENT_GROUP,
):
    for entry in group.entries:
        assert entry.group is None
        entry.group = group
