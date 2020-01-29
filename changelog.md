# Global Slot INI Changelog

## Mark Wickline | 2020-01-23 | v 1.1
### Changed
- in createSlotFromDialogue method, the Y cell count is now incremented down until all cells fit in the tool area.
### Added
- Some fields in the slotUpdate dialog are set to "readonly".
- Connection to OT database created to save slots in `vitrodb_slots` table.

## Mark Wickline | 2020-01-29 | master
### Added
- clean.py, a script to run every Sunday morning that cleans up the database as well as files no the 3D drive.
- Saving layer to slot table in order tracker from the slot app.