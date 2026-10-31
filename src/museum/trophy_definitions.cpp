// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/trophy_definitions.hpp"
#include "museum/localization.hpp"
#include <utility>
namespace museum {
std::vector<TrophyDefinition> make_trophy_definitions() {
    std::vector<TrophyDefinition> out;
    out.reserve(58);


    { TrophyDefinition d;
      d.id="milestone_100";
      d.badge="milestone_100";
      d.title=std::string(i18n::tr("Nothing gathers dust"));
      d.description=std::string(i18n::tr("Open 100 different museum stories."));
      d.rank=TrophyRank::Bronze; d.trigger=TrophyTrigger::VisitCount; d.target=100;
      out.push_back(std::move(d)); }


    { TrophyDefinition d;
      d.id="milestone_300";
      d.badge="milestone_300";
      d.title=std::string(i18n::tr("Just one more gallery…"));
      d.description=std::string(i18n::tr("Open 300 different museum stories."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::VisitCount; d.target=300;
      out.push_back(std::move(d)); }


    { TrophyDefinition d;
      d.id="milestone_600";
      d.badge="milestone_600";
      d.title=std::string(i18n::tr("The museum after midnight"));
      d.description=std::string(i18n::tr("Open 600 different museum stories."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::VisitCount; d.target=600;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="milestone_700";
      d.badge="milestone_700";
      d.title=std::string(i18n::tr("An extra life for memory"));
      d.description=std::string(i18n::tr("Open 700 different museum stories."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::VisitCount; d.target=700;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="milestone_800";
      d.badge="milestone_800";
      d.title=std::string(i18n::tr("Keeper of worlds"));
      d.description=std::string(i18n::tr("Open 800 different museum stories."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::VisitCount; d.target=800;
      out.push_back(std::move(d)); }





    { TrophyDefinition d;
      d.id="milestone_1400";
      d.badge="milestone_1400";
      d.title=std::string(i18n::tr("Horizons without a frame"));
      d.description=std::string(i18n::tr("Open 1400 different museum stories."));
      d.rank=TrophyRank::Gold; d.trigger=TrophyTrigger::VisitCount; d.target=1400;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="milestone_1500";
      d.badge="milestone_1500";
      d.title=std::string(i18n::tr("A world, one voice at a time"));
      d.description=std::string(i18n::tr("Open 1500 different museum stories."));
      d.rank=TrophyRank::Gold; d.trigger=TrophyTrigger::VisitCount; d.target=1500;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="all_catalog";
      d.badge="all_catalog";
      d.title=std::string(i18n::tr("So nothing is lost"));
      d.description=std::string(i18n::tr("Open every story in your saved museum collection."));
      d.rank=TrophyRank::Gold; d.trigger=TrophyTrigger::AllCatalogSnapshot; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="first_music";
      d.badge="first_music";
      d.title=std::string(i18n::tr("Let the museum play"));
      d.description=std::string(i18n::tr("Listen to a soundtrack for 10 seconds, or to the end if shorter."));
      d.rank=TrophyRank::Bronze; d.trigger=TrophyTrigger::FirstMusic; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="first_video";
      d.badge="first_video";
      d.title=std::string(i18n::tr("A moving memory"));
      d.description=std::string(i18n::tr("Watch a video for 30 seconds, or to the end if shorter."));
      d.rank=TrophyRank::Bronze; d.trigger=TrophyTrigger::FirstVideo; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="maximum_zoom";
      d.badge="maximum_zoom";
      d.title=std::string(i18n::tr("Closer to the picture"));
      d.description=std::string(i18n::tr("Reach maximum zoom in the image viewer."));
      d.rank=TrophyRank::Bronze; d.trigger=TrophyTrigger::MaximumZoom; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="first_culture";
      d.badge="first_culture";
      d.title=std::string(i18n::tr("Beyond the screen"));
      d.description=std::string(i18n::tr("Explore the cultural timeline."));
      d.rank=TrophyRank::Bronze; d.trigger=TrophyTrigger::FirstCulture; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="first_today";
      d.badge="first_today";
      d.title=std::string(i18n::tr("The past had an appointment"));
      d.description=std::string(i18n::tr("Use Today to open a story whose anniversary falls today."));
      d.rank=TrophyRank::Bronze; d.trigger=TrophyTrigger::FirstToday; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="first_pin_3d";
      d.badge="first_pin_3d";
      d.stat_key="museum:first_pin_3d";
      d.title=std::string(i18n::tr("Want to see my collection?"));
      d.description=std::string(i18n::tr("Open a museum pin in the 3D viewer."));
      d.rank=TrophyRank::Bronze; d.trigger=TrophyTrigger::ExperienceStat; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_pong";
      d.badge="exp_pong";
      d.stat_key="paddle:consecutive_returns";
      d.title=std::string(i18n::tr("Fifty returns, one rally"));
      d.description=std::string(i18n::tr("Make 50 consecutive paddle returns in Pong."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=50;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_breakout";
      d.badge="exp_breakout";
      d.stat_key="bricks:bricks_broken";
      d.title=std::string(i18n::tr("An opening in the wall"));
      d.description=std::string(i18n::tr("Break all 32 bricks in Breakout."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=32;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_invaders";
      d.badge="exp_invaders";
      d.stat_key="formation:enemies_destroyed";
      d.title=std::string(i18n::tr("The formation breaks"));
      d.description=std::string(i18n::tr("Destroy all 21 invaders in one formation."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=21;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_pacman";
      d.badge="exp_pacman";
      d.stat_key="maze:pac_dots_cleared";
      d.title=std::string(i18n::tr("Every last Pac-Dot"));
      d.description=std::string(i18n::tr("Collect every Pac-Dot and clear the maze."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_tetris";
      d.badge="exp_tetris";
      d.stat_key="gravity:max_lines_single_piece";
      d.title=std::string(i18n::tr("Three in one"));
      d.description=std::string(i18n::tr("Clear at least 3 lines with a single piece in Tetris."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=3;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_katamari";
      d.badge="exp_katamari";
      d.stat_key="scale:completed";
      d.title=std::string(i18n::tr("Everything comes together"));
      d.description=std::string(i18n::tr("Reach the final size and complete the Katamari experience."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_elite";
      d.badge="exp_elite";
      d.stat_key="wireframe:gates_passed";
      d.title=std::string(i18n::tr("A clear flight line"));
      d.description=std::string(i18n::tr("Fly through all 60 gates in one Elite run."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=60;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_mario";
      d.badge="exp_mario";
      d.stat_key="jump:secret_pipe_descents";
      d.title=std::string(i18n::tr("Down the pipe, up with the curtain"));
      d.description=std::string(i18n::tr("Descend into the secret pipe in the Mario experience."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_celeste";
      d.badge="exp_celeste";
      d.stat_key="dash:completed";
      d.title=std::string(i18n::tr("One dash further"));
      d.description=std::string(i18n::tr("Complete all 5 rooms of the Celeste experience."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_ddr";
      d.badge="exp_ddr";
      d.stat_key="rhythm:completed_without_misses";
      d.title=std::string(i18n::tr("A place inside the beat"));
      d.description=std::string(i18n::tr("Complete the entire rhythm performance without a miss."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="exp_portal";
      d.badge="exp_portal";
      d.stat_key="portals:completed";
      d.title=std::string(i18n::tr("GLaDOS approves. More or less."));
      d.description=std::string(i18n::tr("Complete all 4 Portal chambers."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::ExperienceStat; d.target=1;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_zelda";
      d.badge="secret_01";
      d.owner_id="zelda";
      d.title=std::string(i18n::tr("It's dangerous to go alone!"));
      d.description=std::string(i18n::tr("Open story card 1 of The Legend of Zelda."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_10_10_portal";
      d.badge="secret_02";
      d.owner_id="workbook-10-10-portal";
      d.title=std::string(i18n::tr("The cake is a lie"));
      d.description=std::string(i18n::tr("Open story card 1 of Portal."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_08_21_bioshock";
      d.badge="secret_03";
      d.owner_id="workbook-08-21-bioshock";
      d.title=std::string(i18n::tr("I choose the impossible. I choose Rapture!"));
      d.description=std::string(i18n::tr("Open story card 1 of BioShock."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_5561698";
      d.badge="secret_04";
      d.owner_id="workbook-05-10-uncharted-4-a-thief-s-end";
      d.title=std::string(i18n::tr("Sic parvis magna"));
      d.description=std::string(i18n::tr("Open story card 1 of Uncharted 4: A Thief's End."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_09_25_halo_3";
      d.badge="secret_05";
      d.owner_id="workbook-09-25-halo-3";
      d.title=std::string(i18n::tr("Wake me when you need me"));
      d.description=std::string(i18n::tr("Open story card 1 of Halo 3."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_06_14_the_last_of_us";
      d.badge="secret_06";
      d.owner_id="workbook-06-14-the-last-of-us";
      d.title=std::string(i18n::tr("Endure and survive"));
      d.description=std::string(i18n::tr("Open story card 1 of The Last of Us."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_09_03_metal_gear_solid";
      d.badge="secret_07";
      d.owner_id="workbook-09-03-metal-gear-solid";
      d.title=std::string(i18n::tr("You like Castlevania, don't you?"));
      d.description=std::string(i18n::tr("Open story card 4 of Metal Gear Solid."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=3;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_106289";
      d.badge="secret_08";
      d.owner_id="wikipedia-106289";
      d.title=std::string(i18n::tr("E.T. phone home"));
      d.description=std::string(i18n::tr("Open story card 3 of E.T. the Extra-Terrestrial."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=2;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_super_mario_bros";
      d.badge="secret_10";
      d.owner_id="super-mario-bros";
      d.title=std::string(i18n::tr("Thank you, Mario! But our princess is in another castle!"));
      d.description=std::string(i18n::tr("Open story card 1 of Super Mario Bros.."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_355914";
      d.badge="secret_11";
      d.owner_id="wikipedia-355914";
      d.title=std::string(i18n::tr("The last Metroid is in captivity"));
      d.description=std::string(i18n::tr("Open story card 1 of Super Metroid."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_final_fantasy_vii";
      d.badge="secret_12";
      d.owner_id="final-fantasy-vii";
      d.title=std::string(i18n::tr("A promise beneath the stars"));
      d.description=std::string(i18n::tr("Open story card 1 of Final Fantasy VII."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_1789064";
      d.badge="secret_13";
      d.owner_id="wikipedia-1789064";
      d.title=std::string(i18n::tr("The last ribbon"));
      d.description=std::string(i18n::tr("Open story card 1 of Resident Evil."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_1955720";
      d.badge="secret_14";
      d.owner_id="wikipedia-1955720";
      d.title=std::string(i18n::tr("In my restless dreams, I see that town"));
      d.description=std::string(i18n::tr("Open story card 1 of Silent Hill 2."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_756296";
      d.badge="secret_15";
      d.owner_id="wikipedia-756296";
      d.title=std::string(i18n::tr("What is a man?"));
      d.description=std::string(i18n::tr("Open story card 1 of Castlevania: Symphony of the Night."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_11_11_the_elder_scrolls_v_skyrim";
      d.badge="secret_16";
      d.owner_id="workbook-11-11-the-elder-scrolls-v-skyrim";
      d.title=std::string(i18n::tr("Hey, you. You're finally awake"));
      d.description=std::string(i18n::tr("Open story card 1 of The Elder Scrolls V: Skyrim."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_10_28_fallout_3";
      d.badge="secret_17";
      d.owner_id="workbook-10-28-fallout-3";
      d.title=std::string(i18n::tr("War. War never changes"));
      d.description=std::string(i18n::tr("Open story card 1 of Fallout 3."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_8484";
      d.badge="secret_18";
      d.owner_id="wikipedia-11283085";
      d.title=std::string(i18n::tr("I never asked for this"));
      d.description=std::string(i18n::tr("Open story card 1 of Deus Ex: Human Revolution."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }

    { TrophyDefinition d;
      d.id="secret_wikipedia_12915762";
      d.badge="secret_20";
      d.owner_id="wikipedia-12915762";
      d.title=std::string(i18n::tr("Rip and tear, until it is done"));
      d.description=std::string(i18n::tr("Open story card 1 of Doom."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_80981";
      d.badge="secret_21";
      d.owner_id="wikipedia-80981";
      d.title=std::string(i18n::tr("How appropriate. You fight like a cow"));
      d.description=std::string(i18n::tr("Open story card 1 of The Secret of Monkey Island."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_09_15_undertale";
      d.badge="secret_22";
      d.owner_id="workbook-09-15-undertale";
      d.title=std::string(i18n::tr("Despite everything, it's still you"));
      d.description=std::string(i18n::tr("Open story card 1 of Undertale."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_01_26_mass_effect_2";
      d.badge="secret_23";
      d.owner_id="workbook-01-26-mass-effect-2";
      d.title=std::string(i18n::tr("I'm Commander Shepard, and this is my favorite store on the Citadel"));
      d.description=std::string(i18n::tr("Open story card 1 of Mass Effect 2."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_10_26_red_dead_redemption_2";
      d.badge="secret_24";
      d.owner_id="workbook-10-26-red-dead-redemption-2";
      d.title=std::string(i18n::tr("I gave you all I had"));
      d.description=std::string(i18n::tr("Open story card 1 of Red Dead Redemption 2."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_11_08_death_stranding";
      d.badge="secret_25";
      d.owner_id="workbook-11-08-death-stranding";
      d.title=std::string(i18n::tr("Tomorrow is in your hands"));
      d.description=std::string(i18n::tr("Open story card 1 of Death Stranding."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_1353538";
      d.badge="secret_26";
      d.owner_id="wikipedia-1353538";
      d.title=std::string(i18n::tr("Thank you for releasing me!"));
      d.description=std::string(i18n::tr("Open story card 1 of Spyro the Dragon."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_myst";
      d.badge="secret_27";
      d.owner_id="myst";
      d.title=std::string(i18n::tr("The ending has not yet been written"));
      d.description=std::string(i18n::tr("Open story card 1 of Myst."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_569710";
      d.badge="secret_28";
      d.owner_id="wikipedia-569710";
      d.title=std::string(i18n::tr("No, no, that's not how it happened"));
      d.description=std::string(i18n::tr("Open story card 1 of Prince of Persia: The Sands of Time."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_5069549";
      d.badge="secret_29";
      d.owner_id="daily-04-18";
      d.title=std::string(i18n::tr("Nothing is true. Everything is permitted"));
      d.description=std::string(i18n::tr("Open story card 1 of Assassin's Creed II."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_8569";
      d.badge="secret_30";
      d.owner_id="wikipedia-8569";
      d.title=std::string(i18n::tr("Come get some!"));
      d.description=std::string(i18n::tr("Open story card 1 of Duke Nukem 3D."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_38438490";
      d.badge="secret_31";
      d.owner_id="wikipedia-38438490";
      d.title=std::string(i18n::tr("Wind's howling"));
      d.description=std::string(i18n::tr("Open story card 1 of The Witcher 3: Wild Hunt."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_wikipedia_15888290";
      d.badge="secret_32";
      d.owner_id="wikipedia-15888290";
      d.title=std::string(i18n::tr("I'm in space"));
      d.description=std::string(i18n::tr("Open story card 1 of Portal 2."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }
    { TrophyDefinition d;
      d.id="secret_workbook_09_22_dark_souls";
      d.badge="secret_33";
      d.owner_id="workbook-09-22-dark-souls";
      d.title=std::string(i18n::tr("If only I could be so grossly incandescent!"));
      d.description=std::string(i18n::tr("Open story card 1 of Dark Souls."));
      d.rank=TrophyRank::Silver; d.trigger=TrophyTrigger::SecretCard; d.target=1;
      d.secret=true;
      d.card_index=0;
      out.push_back(std::move(d)); }

    { TrophyDefinition d;
      d.id="museum_vip_club";
      d.badge="vip_club";
      d.title=std::string(i18n::tr("Pixel Museum VIP Club"));
      d.description=std::string(i18n::tr("Unlock every other museum trophy."));
      d.rank=TrophyRank::Platinum; d.trigger=TrophyTrigger::AllOtherTrophies; d.target=57;
      out.push_back(std::move(d)); }
    return out;
}
} // namespace museum
