# Portal: an authored momentum puzzle

The study keeps a minimal side view and three original rooms. The first demonstrates a wall crossing, the second redirects a fall into horizontal travel, and the third requires carrying a cube through a floor-to-floor portal and releasing it on an upper pressure plate. The plate opens a real collision barrier. Removing the cube closes it again; reaching the upper platform alone does not finish the room. The cube also has independent gravity, wall/floor collision and speed-preserving portal traversal when released.

The right stick or touchpad chooses among marked surfaces. The triggers place the two portals, the jump action jumps only from solid ground, and the carry/drop action handles a nearby cube. Bottom hints display actual controller glyphs. The article card explains the experiment; no additional prerun screen or textual in-game headings were introduced.

The dotted trajectory runs the same collision and portal integrator on an isolated copy of the current state, assuming the present movement input continues. Its fixed arrays allocate no memory in the update loop. Selection, placement, door and completion visuals animate continuously. Placement, crossing, pressure-plate contact and completion produce distinct tactile events; physical controller response is still unmeasured.

`bash tests/study-portals/run.sh` solves every room using actual control inputs at 30, 60 and 120 Hz, checks portal energy conservation, cube pickup/drop and plate causality, a physically closed door, wrong-orientation and jump-spam failures, touch/focus/reconnect and trigger latches, forecast parity with actual frame integration, and 18000 finite mixed-room input frames. Four real3840?2160EGL renders check GL errors and the glyph footer. These simulation-rate tests do not establish PS5 framerate or hardware feedback.

The existing `tests/study-space/run.sh` regression and21-experience metadata export also pass. Evidence is in `build/research/portal-refined/verification.json` and the referenced logs.
