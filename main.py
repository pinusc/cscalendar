#!/usr/env python
import yaml
from datetime import datetime as dt
import datetime
from icalendar import Calendar, Event
import csv
import re
import argparse
import copy

def daterange(start, stop, step=datetime.timedelta(days=1), inclusive=False):
    # inclusive=False to behave like range by default
    if step.days > 0:
        while start < stop:
            yield start
            start = start + step
            # not +=! don't modify object passed in if it's mutable
            # since this function is not restricted to
            # only types from datetime module
    elif step.days < 0:
        while start > stop:
            yield start
            start = start + step
            if inclusive and start == stop:
                yield start


def sanitize(string):
    return string.lower().strip()


def generate_classes(name, classes):
    name = sanitize(name)
    for block in "ABCDEF":
        if block in classes.keys() and classes[block]:
            continue
        with open("block%s.csv" % block) as blockfile:
            reader = csv.reader(blockfile)
            subjects = next(reader)
            next(reader)  # Teachers
            next(reader)  # Rooms
            for row in reader:
                r = [sanitize(i) for i in row]
                if name in r:
                    classes[block] = subjects[r.index(name)]
                    break
    if "G" not in classes.keys() and "H" not in classes.keys():
        with open("tok.csv") as tokfile:
            reader = csv.reader(tokfile)
            groups = next(reader)
            next(reader)  # Rooms
            for row in reader:
                r = [sanitize(i) for i in row]
                if name in r:
                    block = re.findall(r"Gr.+Block (\w)", groups[r.index(name)])
                    classes[block[0]] = groups[r.index(name)]
                    break
    return classes


def generate_day(idate, schedule, classes):
    """TODO: Docstring for generate_day.
    :returns: TODO

    """
    time = datetime.time(7)
    for i, block in enumerate(schedule):
        time = time.replace(time.hour + 1)
        if block == "@" or block not in classes or not classes[block]:
            continue
        evt = Event()
        evt['dtstart'] = idate.strftime("%Y%m%d") + "T" \
            + time.strftime("%H%M") + "00"
        evt['dtend'] = idate.strftime("%Y%m%d") + "T" \
            + time.replace(time.hour, time.minute + 50).strftime("%H%M") + "00"

        if i is 2 or i is 3 and block is not 'L':
            evt['dtstart'] = "%sT%s00" % \
                (idate.strftime("%Y%m%d"),
                 time.replace(time.hour, time.minute+10).strftime("%H%M"))
            evt['dtend'] = "%sT%s00" % \
                (idate.strftime("%Y%m%d"),
                 time.replace(time.hour + 1).strftime("%H%M"))

        evt['summary'] = classes[block]
        evt['uid'] = 'CSCCAL' + evt['dtstart']
        yield evt


def main():
    """TODO: Docstring for main.
    :name: str, your name
    :DP: str, (PRE, DP1, DP2)
    :calendar: str, the name of the file containig
        the school calendar dates (when there is school)
    :timetable: str, the name of the file containing the school timetable
    :spreadsheet: str, the nema of the spreadsheet file with the classes
    :TOK: bool, true=G, false=H
    :returns: TODO
    """
    # evt = Event()
    # evt['dtstart'] = '20170831T190000'
    # evt['uid'] = '42'
    # evt['status'] = 'CANCELLED'
    # cal.add_component(evt)
    desc = """
    Generates two iCal files: a first one to import all the events in your calendar, and a second one to undo in case you screw up.
    Supports automatically fetching block and tok group information from
    official .xlsx files (converted in .csv).  """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('Name',
                        help='Your name, as it appears on the official'
                        'timetable (case insensitive)'
                        '(if your name appears in more than one fashion,'
                        'please override all blocks)')
    parser.add_argument('DP', help='Your grade',
                        choices=["preDP", "DP1", "DP2"])
    parser.add_argument('-a', dest="blockA", help='Override block A')
    parser.add_argument('-b', dest="blockB", help='Override block B')
    parser.add_argument('-c', dest="blockC", help='Override block C')
    parser.add_argument('-d', dest="blockD", help='Override block D')
    parser.add_argument('-e', dest="blockE", help='Override block E')
    parser.add_argument('-f', dest="blockF", help='Override block F')
    parser.add_argument('--tokGroup',
                        dest="blockT",
                        help='Override ToK Block', choices=["G", "H"])
    parser.add_argument('--tokString',
                        dest="TOKstr", help='Override ToK Block')
    parser.add_argument('--timetable', help='timetable file')
    parser.add_argument('--calendar', help='calendar file')
    parser.add_argument('--output', help='the output\'s file name')
    parser.add_argument('--output_del', help='the delete output\'s file name')
    nsp = parser.parse_args()
    name = nsp.Name
    DP = nsp.DP
    timetable = nsp.timetable or "timetable.yml"
    calendar = nsp.calendar or "calendar.yml"
    empty_classes = {
        'A': nsp.blockA,
        'B': nsp.blockB,
        'C': nsp.blockC,
        'D': nsp.blockD,
        'E': nsp.blockE,
        'F': nsp.blockF,
        'L': "Lunch"
    }
    if nsp.blockT:
        empty_classes[nsp.blockT] = nsp.TOKstr or "TOK"
    with open("cal.ics", 'wb') as fcal, \
            open("dcal.ics", 'wb') as fdcal, \
            open(timetable) as timetable, \
            open(calendar) as calendar:

        timetable = yaml.load(timetable)[DP]
        calendar = yaml.load(calendar)['calendar']
        begin = dt.strptime(str(calendar['begin']), "%Y%m%d")
        end = dt.strptime(str(calendar['end']), "%Y%m%d")
        holidays = []
        for holy in calendar['holidays']:
            hbegin = dt.strptime(str(holy["begin"]), "%Y%m%d")
            hend = dt.strptime(str(holy["end"]), "%Y%m%d")
            holidays += [i for i in daterange(hbegin, hend, inclusive=True)]

        cal = Calendar()
        dcal = Calendar()
        nday = 0  # The next day, i.e. the day tbd, 0-indexed
        nfri = 1  # The ext friday, i.e. the fri tbd
        classes = generate_classes(name, empty_classes)
        for idate in [d for d in daterange(begin, end, inclusive=True)
                      if d not in holidays]:
            wday = idate.isoweekday()  # monday = 1, sunday = 7
            schedule = None
            if 1 <= wday <= 4:  # Mon to Fri
                schedule = timetable[nday+1]
                nday = (nday + 1) % 6
            elif wday == 5:
                schedule = timetable['F' + str(nfri + 1)]
                nfri = not nfri
            else:
                continue
            for block in generate_day(idate, schedule, classes):
                cal.add_component(block)
                b = copy.copy(block)
                b['status'] = "CANCELLED"
                dcal.add_component(b)

        fcal.write(cal.to_ical())
        fdcal.write(dcal.to_ical())

if __name__ == "__main__":
    main()
