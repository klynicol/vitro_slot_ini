# Global Slot INI Changelog

## Mark Wickline | 2020-01-23 | v 1.1
### Changed
- in createSlotFromDialogue method, the Y cell count is now incremented down until all cells fit in the tool area.
### Added
- Some fields in the slotUpdate dialog are set to "readonly".
- Connection to OT database created to save slots in `vitrodb_slots` table.

## Mark Wickline | 2020-01-29 | v 1.2 & v 1.3
### Added
- clean.py, a script to run every Sunday morning that cleans up the database as well as files no the 3D drive.
- Saving layer to slot table in order tracker from the slot app.
- Created a datetime stamped backup of slots.ini whenever the application is opened.
### Fixed
- When updating a slot to include cells, the proper cell width and height will be stored now.

## Mark Wickline | 2020-02-12 | scripts
### Changed
- in savejob.py changed the break folder further back in the chain to allow files from different folders to be
added.