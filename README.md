# dronereg
---

## Overview

Extract all registered and deregistered drones from the [FAA Aircraft Registration Database](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download).

Running the script will generate a csv file with the following information:
```
COLUMN              SOURCE FILES   DESCRIPTION
=================   ============   ===================================================================================
n_number            M, D           Identification number assigned to aircraft
serial_number       M, D           Aircraft Serial Number
mode_s_code         M, D           Aircraft transponder code
mode_s_code_hex     M, D           Aircraft transponder code in hex
mfr_mdl_code        M, D           A code assigned to the aircraft manufacturer model and series
mfr                 A              Aircraft manufacturer
model               A              Aircraft model and series
no_eng              A              Number of engines on the aircraft
ac_weight           A              Aircraft maximum gross take off weight in pounds
                                   - CLASS 1: Up to 12,499
                                   - CLASS 2: 12,500 to 19,000
                                   - CLASS 3: 20,000 and over
                                   - CLASS 4: UAV and up to 55
type_registrant     M, D           Aircraft registrant type
city                M, D           Registrant city
state               M, D           Registrant state
zip_code            M, D           Registrant zip code
status              M, D           The status of the aircraft's certification of registration
cert_issue_date     M, D           Date the Aircraft Registrant Branch issued the Certificate of Aircraft Registration
airworthiness_date  M, D           Date of airworthiness
last_action_date    M, D           Date of last action
cancel_date         D              Date of cancellation (deregistered drones only)

SOURCE FILES: M = MASTER.txt A = ACFTREF.txt D = DEREG.txt
```


## Usage

```
usage: dronereg.py [-h] [--save_db] [-db DATABASE] [--data_dir DATA_DIR]

options:
  -h, --help            show this help message and exit
  --save_db
                                Download and save the Aircraft Registration Database

  -db DATABASE, --database DATABASE

                                File path of the Aircraft Registration Database

  --data_dir DATA_DIR
                                Directory where the Aircraft Registration Database and/or the extracted
                                drone registration csv file will be saved

                                Defaults to current working directory
```

## Examples

Extract drone data from the most up to date aircraft registration database:
```
$ python3 dronereg.py
```

Extract drone data from an already downloaded database:
```
$ python3 dronereg.py -db ReleasableAircraft.zip
```
