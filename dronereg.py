#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import csv
import io
import re
import time
import zipfile
from pathlib import Path

try:
  import requests
  _has_requests = True
except ImportError:
  import urllib.request
  import urllib.error
  _has_requests = False


# ** Database **
class ReleasableAircraft:
  URL = 'https://registry.faa.gov/database/ReleasableAircraft.zip'

  # ardata.pdf - page 1
  REGISTRANT_TYPES = {
      '1': 'Individual',
      '2': 'Partnership',
      '3': 'Corporation',
      '4': 'Co-Owned',
      '5': 'Government',
      '7': 'LLC',
      '8': 'Non Citizen Corporation',
      '9': 'Non Citizen Co-Owned',
  }

  # ardata.pdf - pages 5-7
  STATUS_CODES = {
      '1': 'Triennial Aircraft Registration form was returned by the Post Office as undeliverable',
      '2': 'N-Number Assigned but has not yet been registered',
      '3': 'N-Number assigned as a Non Type Certificated aircraft - but has not yet been registered',
      '4': 'N-Number assigned as import - but has not yet been registered',
      '5': 'Reserved N-Number',
      '6': 'Administratively canceled',
      '7': 'Sale reported',
      '8': 'A second attempt has been made at mailing a Triennial Aircraft Registration form to the owner with no response',
      '9': 'Certificate of Registration has been revoked',
      '10': 'N-Number assigned but has not been registered and is pending cancellation',
      '11': 'N-Number assigned as a Non Type Certificated (Amateur) but has not been registered that is pending cancellation',
      '12': 'N-Number assigned as import but has not been registered that is pending cancellation',
      '13': 'Registration Expired',
      '14': 'First Notice for ReRegistration/Renewal',
      '15': 'Second Notice for ReRegistration/Renewal',
      '16': 'Registration Expired - Pending Cancellation',
      '17': 'Sale Reported - Pending Cancellation',
      '18': 'Sale Reported - Canceled',
      '19': 'Registration Pending - Pending Cancellation',
      '20': 'Registration Pending - Canceled',
      '21': 'Revoked - Pending Cancellation',
      '22': 'Revoked - Canceled',
      '23': 'Expired Dealer (Pending Cancellation)',
      '24': 'Third Notice for ReRegistration/Renewal',
      '25': 'First Notice for Registration Renewal',
      '26': 'Second Notice for Registration Renewal',
      '27': 'Registration Expired',
      '28': 'Third Notice for Registration Renewal',
      '29': 'Registration Expired - Pending Cancellation',
      'A': 'The Triennial Aircraft Registration form was mailed and has not been returned by the Post Office',
      'D': 'Expired Dealer',
      'E': 'The Certificate of Aircraft Registration was revoked by enforcement action',
      'M': 'Aircraft registered to the manufacturer under their Dealer Certificate',
      'N': 'Non-citizen Corporations which have not returned their flight hour reports',
      'R': 'Registration pending',
      'S': 'Second Triennial Aircraft Registration Form has been mailed and has not been returned by the Post Office ',
      'T': 'Valid - from Trainee',
      'V': 'Valid',
      'X': 'Enforcement Letter',
      'Z': 'Permanent Reserved',
      '': 'Invalid',
  }

  def __init__(self, database_path: Path | None = None):
    self.database_path = database_path
    if self.database_path:
      with open(self.database_path, 'rb') as f:
        self._database = f.read()
    else:
      self._database = self.download()

  def download(self):
    if _has_requests:
      try:
        r = requests.get(self.URL)
        return r.content
      except requests.exceptions.RequestException as e:
        print(f'Error downloading database: {e}')
        raise e
    else:
      try:
        with urllib.request.urlopen(self.URL) as res:
          return res.read()
      except urllib.error.URLError as e:
        print(f'Error downloading database: {e}')
        raise e

  def save(self, database_path: Path | None = None):
    database_path = database_path or Path.cwd() / 'ReleasableAircraft.zip'
    try:
      with open(database_path, 'wb') as f:
        f.write(self._database)
        self.database_path = database_path
        print(f'Saved database to: {database_path}')
    except Exception as e:
      print(f'Error saving database: {e}')

  def list_files(self):
    with zipfile.ZipFile(io.BytesIO(self._database), 'r') as zfile:
      for file in zfile.namelist():
        print(file)

  @staticmethod
  def _tidy_header(text: str):
    text = text.strip().lower()
    text = re.sub(r'\(|\)', '', text)
    text = re.sub(r'-| ', '_', text)
    return text

  def read_file(self, file: str):
    with zipfile.ZipFile(io.BytesIO(self._database), 'r') as zfile:
      with zfile.open(file) as f:
        reader = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig'))
        header = [self._tidy_header(x) for x in next(reader)[:-1]]
        row = collections.namedtuple('row', header)
        for r in reader:
          dat = [x.strip() for x in r[:-1]]
          if len(dat) == len(header):
            yield row(*dat)

  @staticmethod
  def format_date(dt: str | None = None):
    return time.strftime('%Y-%m-%d', time.strptime(dt, '%Y%m%d')) if dt else ''

  @staticmethod
  def format_zip(zip: str | None = None):
    return f'{zip[:5]}-{zip[5:]}' if (zip and len(zip) == 9) else zip


# ** Drone **
DRONE_AIRCRAFT_TYPE = '6'  # rotorcraft
DRONE_ENGINE_TYPE = '10'  # electric

DRONE_DATA_HEADERS = [
    'n_number',
    'serial_number',
    'mode_s_code',
    'mode_s_code_hex',
    'mfr_mdl_code',
    'mfr',
    'model',
    'no_eng',
    'ac_weight',
    'type_registrant',
    'city',
    'state',
    'zip_code',
    'status',
    'cert_issue_date',
    'airworthiness_date',
    'last_action_date',
    'cancel_date',
]


def is_drone(acft_type: str, eng_type: str):
  return (
      acft_type == DRONE_AIRCRAFT_TYPE
  ) and (
      eng_type == DRONE_ENGINE_TYPE
  )


def parse_drone_data(outfile: Path, database_path: Path | None = None):
  ra = ReleasableAircraft(database_path=database_path)

  # ACFTREF.txt - drone manufacturer and model lookup
  mfr_mdls = {
      mm.code: mm for mm in ra.read_file('ACFTREF.txt')
      if is_drone(mm.type_acft, mm.type_eng)
  }

  with open(outfile, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(DRONE_DATA_HEADERS)

    # MASTER.txt
    for ac in ra.read_file('MASTER.txt'):
      if not is_drone(ac.type_aircraft, ac.type_engine):
        continue
      # lookup manufacturer and model
      mfr_mdl = mfr_mdls.get(ac.mfr_mdl_code)
      if mfr_mdl:
        writer.writerow([
            ac.n_number,
            ac.serial_number,
            ac.mode_s_code,
            ac.mode_s_code_hex,
            ac.mfr_mdl_code,
            mfr_mdl.mfr,
            mfr_mdl.model,
            mfr_mdl.no_eng,
            mfr_mdl.ac_weight,
            ra.REGISTRANT_TYPES.get(ac.type_registrant, ''),
            ac.city,
            ac.state,
            ra.format_zip(ac.zip_code),
            ra.STATUS_CODES.get(ac.status_code, ''),
            ra.format_date(ac.cert_issue_date),
            ra.format_date(ac.air_worth_date),
            ra.format_date(ac.last_action_date),
            '',  # cancel date - DEREG only
        ])

    # DEREG.txt
    for ac in ra.read_file('DEREG.txt'):
      # lookup manufacturer and model
      mfr_mdl = mfr_mdls.get(ac.mfr_mdl_code)
      if mfr_mdl:
        writer.writerow([
            ac.n_number,
            ac.serial_number,
            ac.mode_s_code,
            ac.mode_s_code_hex,
            ac.mfr_mdl_code,
            mfr_mdl.mfr,
            mfr_mdl.model,
            mfr_mdl.no_eng,
            mfr_mdl.ac_weight,
            ra.REGISTRANT_TYPES.get(ac.indicator_group, ''),
            ac.city_mail,
            ac.state_abbrev_mail,
            ra.format_zip(ac.zip_code_mail),
            ra.STATUS_CODES.get(ac.status_code, ''),
            ra.format_date(ac.cert_issue_date),
            ra.format_date(ac.air_worth_date),
            ra.format_date(ac.last_act_date),
            ra.format_date(ac.cancel_date),
        ])

  print(f'Saved drone data to: {outfile}')


def _valid_dir(path: Path | str):
  if not isinstance(path, Path):
    path = Path(path)
  if not path.exists() or not path.is_dir():
    raise argparse.ArgumentTypeError(f'Invalid directory path: {path}')
  return path


def _valid_file(path: Path | str):
  if not isinstance(path, Path):
    path = Path(path)
  if not path.exists():
    raise argparse.ArgumentTypeError(f'Invalid file path: {path}')
  return path


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawTextHelpFormatter,
  )

  parser.add_argument(
      '--save_db',
      action='store_true',
      help='''
        Download and save the Aircraft Registration Database
        ''',
  )

  parser.add_argument(
      '-db',
      '--database',
      type=_valid_file,
      help='''
        File path of the Aircraft Registration Database
        ''',
  )

  parser.add_argument(
      '--data_dir',
      type=_valid_dir,
      default=Path.cwd(),
      help='''
        Directory where the Aircraft Registration Database and/or the extracted
        drone registration csv file will be saved

        Defaults to current working directory
        ''',
  )

  args = parser.parse_args()

  if args.save_db:
    outfile = args.data_dir / 'ReleasableAircraft.zip'
    ra = ReleasableAircraft()
    ra.save(database_path=outfile)
  else:
    outfile = args.data_dir / 'ReleasableDrone.csv'
    parse_drone_data(database_path=args.database, outfile=outfile)


if __name__ == '__main__':
  main()
