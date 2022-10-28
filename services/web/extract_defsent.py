import sys
import os
import shutil
import atexit
import tempfile
import subprocess
import argparse
import json
import time
import re
import multiprocessing as mp

import conllu


termex_perl = 'SentEx_patternsF.pl'
termex_pattern1 = 'JeStaSoPatterns_finishOK.txt'
input_fname = 'input.lines'
output_union = 'outunion.txt'



#def cleanup(tempdir):
    #if isinstance(tempdir, tempfile.TemporaryDirectory):
        #print(f'INFO: Removing temporary folder: {tempdir.name}', file=sys.stderr)
        #tempdir.cleanup()


def words_search(words_string, sentence_string):
    #words_string = " " + words_string.strip() + " "
    #sentence_string = " " + sentence_string.strip() + " "
    words_string = " " + words_string + " "
    sentence_string = " " + sentence_string + " "
    return sentence_string.find(words_string)


# this search works for searching single whitespace joined words in other single whitespace joined words
# See here (https://docs.python.org/3/library/re.html) for the definition of \b
# NOTE: this is slow!
def find_words_in_string(words, string):
    if re.search(r"\b" + re.escape(words) + r"\b", string):
        return True
    return False


# returns all non-overlapping starting sublist positions
def sublist(lst, sub):
    elt = sub[0]
    pos = 0
    allpos = []
    while lst != []:
        if elt in lst:
            idx = lst.index(elt)
            pos += idx
            if lst[idx: idx + len(sub)] == sub:
                allpos.append(pos)
                lst = lst[idx + len(sub):]
                pos += len(sub)
                # return pos
            else:
                lst = lst[idx + 1:]
                pos += 1
        else:
            break
            # return -1
    return allpos
    # return -1


# returns first sublist position or -1
def is_sublist(lst, sub):
    elt = sub[0]
    pos = 0
    while lst != []:
        if elt in lst:
            idx = lst.index(elt)
            pos += idx
            if lst[idx: idx + len(sub)] == sub:
                return pos
            else:
                lst = lst[idx + 1:]
                pos += 1
        else:
            return -1
    return -1


def split_conllu_file(conllu_file, n):
    tempdir = tempfile.TemporaryDirectory()
    #print('-->', tempdir.name)

    parts = [[] for i in range(n)]
    with open(conllu_file, 'r', encoding="utf-8") as ifp:
        for i, sent in enumerate(conllu.parse_incr(ifp)):
            parts[i%n].append(sent)

    outfiles = [os.path.join(tempdir.name, f'{i}.conllu') for i in range(n)]
    for fname, sentences in zip(outfiles, parts):
        with open(fname, 'w') as fp:
            for s in sentences:
                fp.write(s.serialize())
    return tempdir, outfiles


def read_terms_json_file(fname):
    with open(fname) as fp:
        lem_terms = json.load(fp)

    if 'lemmatized_terms' not in lem_terms or not isinstance(lem_terms['lemmatized_terms'], list):
        raise Exception('''Invalid JSON format for terms, must be like {"lemmatized_terms": ["first term", "second term", ...]}.''')
    return [str(x).strip() for x in lem_terms['lemmatized_terms']]



def extract_definition_sentences(conllu_file, terms=[]):
    # initialize temp directory
    tempdir = tempfile.TemporaryDirectory()

    st = time.time()

    # prepare input data in correct format
    with open(conllu_file, 'r', encoding="utf-8") as ifp:
        with open(os.path.join(tempdir.name, input_fname), 'w') as ofp:
            for i, sent in enumerate(conllu.parse_incr(ifp)):
                if terms != []:
                    lem_sent = ' '.join([tok['lemma'] for tok in sent])
                    for term in terms:
                        if term in lem_sent: # first test: string search, can lead to false results (substrings, not whole words)
                            term_tokens = term.split()
                            lem_tokens = [tok['lemma'] for tok in sent]
                            if is_sublist(lem_tokens, term_tokens) != -1:  #slower exact testing
                                # if words_search(term, lem_sent) != -1:
                                # if is_sublist(lem_tokens, term) != -1:
                                # if find_words_in_string(term, lem_sent):
                                # if term in lem_sent:
                                #if len(term)>1:
                                # print('--->', term, lem_tokens)
                                for tok in sent:
                                    print(f"{tok['form']}\tTOK\t{tok['lemma']}\t{tok['xpos']}", file=ofp)
                                sid = sent.metadata.get('sent_id', i)
                                print(f'''\t\t\t<S sid_sp="{sid}" aid_sp="{conllu_file}" defvalue=""/>\n''', file=ofp)
                else:
                    for tok in sent:
                        print(f"{tok['form']}\tTOK\t{tok['lemma']}\t{tok['xpos']}", file=ofp)
                    sid = sent.metadata.get('sent_id', i)
                    print(f'''\t\t\t<S sid_sp="{sid}" aid_sp="{conllu_file}" defvalue=""/>\n''', file=ofp)

    #print('Preparation and filtering time: ', time.time() - st)
    st = time.time()

    for fn in [termex_perl, termex_pattern1]:
        shutil.copyfile(fn, os.path.join(tempdir.name, fn))

    # run extractor
    p = subprocess.run(['perl', termex_perl, input_fname, termex_pattern1],
                       stderr=subprocess.DEVNULL,
                       cwd=tempdir.name)

    if p.returncode != 0:
        raise IOError('Term extraction process failed, check its perl script.')

    resultfile = os.path.join(tempdir.name, output_union)
    if not os.path.exists(resultfile):
        raise IOError('Output file with union of results does not exist: {resultfile}')

    #print('Extraction time: ', time.time() - st)

    lines = open(resultfile).read()
    return [line.split('###')[0].strip() for line in lines.split('\n') if line.strip()]


def mp_extract(conllu, terms, ncores=os.cpu_count()):
    defs = []
    conllu_tempdir, conllu_part_files = split_conllu_file(conllu, ncores)
    with mp.Pool(ncores) as pool:
        params = zip(conllu_part_files, [terms] * len(conllu_part_files))
        for i, result in enumerate(pool.starmap(extract_definition_sentences, params)):
            defs.extend(result)

    return sorted(list(set(defs)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('CoNLLU_file', help='Input file in CoNLL-U format')
    parser.add_argument('-n', '--ncpu', type=int, help='Number of CPU cores to use. Leave empty to use all cores.')
    parser.add_argument('-t', '--terms', help='Optional input file with lemmatized terms for filtering the input file, formatted like this: {"lemmatized_terms": ["first term", "second term", ...]} ')
    args = parser.parse_args()

    #sents = extract_definition_sentences(args.CoNLLU_file)
    #print('\n'.join(list(set(sents))))

    ncores = args.ncpu if args.ncpu is not None else os.cpu_count()
    lem_terms = read_terms_json_file(args.terms) if args.terms else []

    defs = mp_extract(args.CoNLLU_file, lem_terms, ncores)
    for s in defs:
        print(s)
