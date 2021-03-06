#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
:mod:`Quantulum` tests.
'''

# Standard library
import os
import re
import sys
import json
import unittest

# Dependences
import wikipedia

# Quantulum
from . import load as l
from . import parser as p
from . import classes as c
from . import classifier as clf

COLOR1 = '\033[94m%s\033[0m'
COLOR2 = '\033[91m%s\033[0m'
TOPDIR = os.path.dirname(__file__) or "."


################################################################################
def wiki_test(page='CERN'):
    '''
    Download a wikipedia page and test the parser on its content.
    Pages full of units:
        CERN
        Hubble_Space_Telescope,
        Herschel_Space_Observatory
    '''

    content = wikipedia.page(page).content
    parsed = p.parse(content)
    parts = int(round(len(content) * 1.0 / 1000))

    print()
    end_char = 0
    for num, chunk in enumerate(range(parts)):
        _ = os.system('clear')
        print()
        qua = [
            j for j in parsed if chunk * 1000 < j.span[0] < (chunk + 1) * 1000
        ]
        beg_char = max(chunk * 1000, end_char)
        if qua:
            end_char = max((chunk + 1) * 1000, qua[-1].span[1])
            text = content[beg_char:end_char]
            shift = 0
            for quantity in qua:
                index = quantity.span[1] - beg_char + shift
                to_add = COLOR1 % (' {' + str(quantity) + '}')
                text = text[0:index] + to_add + COLOR2 % text[index:]
                shift += len(to_add) + len(COLOR2) - 6
        else:
            text = content[beg_char:(chunk + 1) * 1000]
        print(COLOR2 % text)
        print()
        try:
            _ = input('--------- End part %d of %d\n' % (num + 1, parts))
        except (KeyboardInterrupt, EOFError):
            return


################################################################################
def load_tests(ambiguity=True):
    '''
    Load all tests from tests.json.
    '''

    path = os.path.join(TOPDIR, 'tests.ambiguity.json'
                        if ambiguity else 'tests.json')
    with open(path, 'r') as test_file:
        tests = json.load(test_file)

        for test in tests:
            res = []
            for item in test['res']:
                try:
                    unit = l.NAMES[item['unit']]
                except KeyError:
                    try:
                        entity = item['entity']
                    except KeyError:
                        print(('Could not find %s, provide "derived" and'
                               ' "entity"' % item['unit']))
                        return
                    if entity == 'unknown':
                        derived = [{
                            'base': l.NAMES[i['base']].entity.name,
                            'power': i['power']
                        } for i in item['dimensions']]
                        entity = c.Entity(name='unknown', dimensions=derived)
                    elif entity in l.ENTITIES:
                        entity = l.ENTITIES[entity]
                    else:
                        print(('Could not find %s, provide "derived" and'
                               ' "entity"' % item['unit']))
                        return
                    unit = c.Unit(
                        name=item['unit'],
                        dimensions=item['dimensions'],
                        entity=entity)
                try:
                    span = next(
                        re.finditer(re.escape(item['surface']),
                                    test['req'])).span()
                except StopIteration:
                    print('Surface mismatch for "%s"' % test['req'])
                    return
                uncert = None
                if 'uncertainty' in item:
                    uncert = item['uncertainty']
                res.append(
                    c.Quantity(
                        value=item['value'],
                        unit=unit,
                        surface=item['surface'],
                        span=span,
                        uncertainty=uncert))
            test['res'] = [i for i in res]

        return tests


################################################################################
class EndToEndTests(unittest.TestCase):
    """Test suite for the quantulum3 project."""

    def test_load_tests(self):
        self.assertFalse(load_tests() is None)

    def test_parse_classifier(self):
        all_tests = load_tests(False) + load_tests(True)
        # forcedly activate classifier
        clf.USE_CLF = True
        for test in sorted(all_tests, key=lambda x: len(x['req'])):
            quants = p.parse(test['req'])
            self.assertEqual(
                quants, test['res'],
                "{} \n {}".format([quant.__dict__ for quant in quants],
                                  [quant.__dict__ for quant in test['res']]))

    def test_parse_no_classifier(self):
        all_tests = load_tests(False)
        # forcedly deactivate classifier
        clf.USE_CLF = False
        for test in sorted(all_tests, key=lambda x: len(x['req'])):
            quants = p.parse(test['req'])
            self.assertEqual(
                quants, test['res'], "\nExcpected: {1} \nGot: {0}".format(
                    [quant.__dict__ for quant in quants],
                    [quant.__dict__ for quant in test['res']]))

    @unittest.skip('Do not retrain classifiers, as overwrites clf.pickle and wiki.json files.')
    def test_training(self):
        # TODO - update test to not overwirte existing clf.pickle and wiki.json files.
        clf.train_classifier(False)
        clf.train_classifier(True)


################################################################################
if __name__ == '__main__':

    unittest.main()
