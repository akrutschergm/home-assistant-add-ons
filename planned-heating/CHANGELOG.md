# Changelog

## 0.5.8

- New: Added log_level config option

## 0.5.7

- New: Save tado refresh token, cached schedules and iCal data in persistent data folder
- New: Cache folder can be set by argument also on non-HA installations.

## 0.5.6

- New: Use refresh token for tado login

## 0.5.5

- Fixed tado day type

## 0.5.4

- Fixed updating tado zones

## 0.5.3

- Fixed: Convert iCal event to local time

## 0.5.2

- Changed that tado schedules are only set when updates are available

## 0.5.1

- Restored churchtools settings as optional settings

## 0.5.0

- Changed config elements - BREAKING!
- Added fixed schedules
- Added iCal support for files and URLs

## 0.4.4

- Fixed not having integrated both fixes

## 0.4.3

- Fixed another bug when getting Tado zone ids

## 0.4.2

- Fixed a bug when getting Tado zone ids

## 0.4.1

- Reduced multiple API calls to get Tado zones

## 0.4.0

- Tado device flow now replaces username and password login procedure

## 0.3.0

- Now runs as Home Assistant add-on
- Changed initialization of logging and added some logging

## 0.2.0

- Added PlannedHeatingWithTado

## 0.1.0

- Initial version
