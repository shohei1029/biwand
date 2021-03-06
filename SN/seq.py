#!/usr/bin/env python3

import numpy as np

from Bio import SeqIO


def read_fastafile(fasta_file):
    with open(fasta_file, 'r') as fa_fh:
        #fa_dict = SeqIO.to_dict(SeqIO.parse(fa_fh, "fasta"))
        fa_dict = seqrcds_to_ordereddict(SeqIO.parse(fa_fh, "fasta"))
    return fa_dict


def read_fasta(fasta_text):
    fa_dict = SeqIO.to_dict(SeqIO.parse(fasta_text, "fasta"))
    return fa_dict


def read_genbank_dir(dir_path):
    """
    input including asterisk,  e.g. "./genomes/*.gbk"
    (generator)
    returns: gen( list of GenBank SeqRecords )
    """
    import glob
    gb_files = glob.glob(dir_path)  #頼むからgenbankファイルしか入れないでくれ..
    for gb_f in gb_files:
        gb = SeqIO.parse(gb_f, "genbank")  #generator object
        yield list(gb)  #List of GenBank SeqRecords


def genbank2fasta(gb_file, fasta_file):
    with open(fasta_file, 'w') as fa_fh:
        for seq_record in SeqIO.parse(gb_file, "genbank"):
            fa_fh.write(">{acc}@{org}\n{seq}\n".format(
                acc=seq_record.id,
                org=seq_record.features[0].qualifiers["organism"][0].replace(
                    " ", "_"),
                seq=seq_record.seq))


def genbankdir2fasta(dir_path, fasta_file):
    """
    input including asterisk,  e.g. "./genomes/*.gbk"
    output fasta like >{acc}@{org}\n{seq}
    """
    import glob
    gb_files = glob.glob(dir_path)  #頼むからgenbankファイルしか入れないでくれ..
    with open(fasta_file, 'w') as fa_fh:
        for gb_f in gb_files:
            for seq_record in SeqIO.parse(gb_f, "genbank"):  #generator object
                fa_fh.write(">{acc}@{org}\n{seq}\n".format(
                    acc=seq_record.id,
                    org=seq_record.features[0].qualifiers["organism"]
                    [0].replace(" ", "_"),
                    seq=seq_record.seq))


def genbankdir2fasta_taxid(dir_path, fasta_file):
    """
    input including asterisk,  e.g. "./genomes/*.gbk"
    output fasta like >{acc}@{org}@taxon|{taxon}\n{seq}
    """
    import glob
    gb_files = glob.glob(dir_path)  #頼むからgenbankファイルしか入れないでくれ..
    with open(fasta_file, 'w') as fa_fh:
        for gb_f in gb_files:
            for seq_record in SeqIO.parse(gb_f, "genbank"):  #generator object

                taxid = ""
                for dbxref in seq_record.features[0].qualifiers["db_xref"]:
                    if "taxon:" in dbxref:
                        taxid = dbxref.split(":")[
                            -1]  # e.g. taxon|121345 for fasta header

                fa_fh.write(">{acc}@{org}@taxon|{taxon}\n{seq}\n".format(
                    acc=seq_record.id,
                    org=seq_record.features[0].qualifiers["organism"]
                    [0].replace(" ", "_"),
                    taxon=taxid,
                    seq=seq_record.seq))


def read_tomlfile(toml_file):
    from collections import OrderedDict
    import toml
    with open(toml_file) as tomlfh:
        toml_d = toml.loads(
            tomlfh.read(),
            OrderedDict)  #取り出す時の順番が毎回同じ方が助かる場合があるから。tomlファイルに記載された順番どおりではない。
    return toml_d


def random_sample_fasta(fa_d, n):
    import random
    fa_sampled_l = random.sample(list(fa_d.items()), n)
    fa_sampled_d = dict()
    for seq in fa_sampled_l:  #データ形式をSeqIOで読み込んだものと同じに戻す
        fa_sampled_d.update({seq[0]: seq[1]})
    return fa_sampled_d


def read_fasta_subtype(fasta_text):
    """
    returns: {subtype: {fasta_header: fasta_seq}}
    """
    from collections import defaultdict
    fasta_d = read_fasta(fasta_text)
    subtypes_d = defaultdict(dict)
    for k, v in fasta_d.items():
        subtype = k.split(":")[-1].split("-")[0]  #ドメイン等の領域が書いてある場合もあるから.
        subtypes_d[subtype].update({k: v})
    return subtypes_d


def seqrcds_to_dict(sequences, key_function=None):  #from BioPython (SeqIO)
    """Turns a sequence iterator or list into a dictionary.

        - sequences  - An iterator that returns SeqRecord objects,
          or simply a list of SeqRecord objects.
        - key_function - Optional callback function which when given a
          SeqRecord should return a unique key for the dictionary.

    e.g. key_function = lambda rec : rec.name
    or,  key_function = lambda rec : rec.description.split()[0]

    If key_function is omitted then record.id is used, on the assumption
    that the records objects returned are SeqRecords with a unique id.

    If there are duplicate keys, an error is raised.
    """
    if key_function is None:
        key_function = lambda rec: rec.id

    d = dict()
    for record in sequences:
        key = key_function(record)
        if key in d:
            raise ValueError("Duplicate key '%s'" % key)
        d[key] = record
    return d


def seqrcds_to_ordereddict(
        sequences, key_function=None,
        ignore_identical_header=False):  #modified to return as OrderedDict
    from collections import OrderedDict
    if key_function is None:
        key_function = lambda rec: rec.id

    d = OrderedDict()
    for record in sequences:
        key = key_function(record)
        if key in d:
            if ignore_identical_header:  #同一ヘッダーがあったときは最初の奴だけを保存する。
                continue
            else:
                raise ValueError("Duplicate key '%s'" % key)
        d[key] = record
    return d


def fetch_genbank_entries_from_acc(gi_list, both_format=False, seqrcd=False):
    """
    If seqrcd=True, returns SeqRecord objects.
    """
    from Bio import Entrez
    Entrez.email = "bio@bioinfo.cn"
    handle = Entrez.efetch(db="nuccore",
                           id=gi_list,
                           rettype="gb",
                           retmode="text")
    if both_format:
        return (handle.read(), SeqIO.parse(handle, "gb"))
    elif seqrcd:
        return SeqIO.parse(handle, "gb")
    else:
        return handle.read()


def taxid2lineage(taxids=[511145, 203267, 221988]):
    '''
    Requires ETE toolkit. If not installed, try "pip install ete3". (http://etetoolkit.org/)

        input: NCBI taxonomy ID e.g. "511145"
        returns: lineage dict including ['superkingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']
            {'superkingdom': 'Bacteria', 'phylum': 'Proteobacteria', 'class': 'Gammaproteobacteria', 
            'order': 'Enterobacterales', 'family': 'Enterobacteriaceae', 'genus': 'Escherichia', 'species': 'Escherichia coli'}

    If you inputs list of ids, this returns list of lineage dict.
    Note: "superkingdom" means "domain".
    '''
    from ete3 import NCBITaxa
    ranks = [
        'superkingdom', 'phylum', 'class', 'order', 'family', 'genus',
        'species'
    ]
    ncbi = NCBITaxa()

    def _taxid2lineage(taxid):
        #ranks = ['superkingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']
        #ncbi = NCBITaxa()
        lineage = ncbi.get_lineage(taxid)
        lineage_dict = dict()
        names = ncbi.get_taxid_translator(lineage)
        for rank in ranks:
            for k, v in ncbi.get_rank(lineage).items():
                if v == rank:
                    lineage_dict.update({v: names[k]})
        return lineage_dict

    if isinstance(taxids, list):
        return [_taxid2lineage(taxid) for taxid in taxids]
    else:
        return _taxid2lineage(taxids)


def cprint(string, color, highlight=False):
    """
    Colored print
    colors:
        red,green,yellow,blue,magenta,cyan,white,crimson

    #冗長につき改良の余地大
    """
    end = "\033[1;m"
    pstr = ""
    if color == "red":
        if highlight:
            pstr += '\033[1;41m'
        else:
            pstr += '\033[1;31m'
    elif color == "green":
        if highlight:
            pstr += '\033[1;42m'
        else:
            pstr += '\033[1;32m'
    elif color == "yellow":
        if highlight:
            pstr += '\033[1;43m'
        else:
            pstr += '\033[1;33m'
    elif color == "blue":
        if highlight:
            pstr += '\033[1;44m'
        else:
            pstr += '\033[1;34m'
    elif color == "magenta":
        if highlight:
            pstr += '\033[1;45m'
        else:
            pstr += '\033[1;35m'
    elif color == "cyan":
        if highlight:
            pstr += '\033[1;46m'
        else:
            pstr += '\033[1;36m'
    elif color == "white":
        if highlight:
            pstr += '\033[1;47m'
        else:
            pstr += '\033[1;37m'
    elif color == "crimson":
        if highlight:
            pstr += '\033[1;48m'
        else:
            pstr += '\033[1;38m'
    else:
        print("Error Unsupported color:" + color)

    print(pstr + string + end)


def draw_annopos(ax, anno_dict, rows=3, readingframe=False, fs=9):
    """
    anno_dict = {name:[start,end]}
    """
    from matplotlib.patches import Rectangle
    y1, height, pad = 0, 1, 0.2
    ax.set_ylim([-pad, rows * (height + pad)])
    anno_elements = []
    for name, x in anno_dict.items():
        anno_elements.append({
            'name': name,
            'x1': x[0],
            'x2': x[1],
            'width': x[1] - x[0]
        })
    anno_elements.sort(key=lambda x: x['x1'])
    for ai, anno in enumerate(anno_elements):
        if readingframe:
            anno['y1'] = y1 + (height + pad) * (2 - (anno['x1']) % 3)
        else:
            anno['y1'] = y1 + (height + pad) * (ai % rows)
        anno['y2'] = anno['y1'] + height

    for anno in anno_elements:
        r = Rectangle((anno['x1'], anno['y1']),
                      anno['width'],
                      height,
                      facecolor=[0.8] * 3,
                      edgecolor='k',
                      label=anno['name'])

        xt = anno['x1'] + 0.5 * anno['width']
        yt = anno['y1'] + 0.2 * height + height * (anno['width'] < 500)

        ax.add_patch(r)
        ax.text(xt, yt, anno['name'], color='k', fontsize=fs, ha='center')


#original -https://github.com/neherlab/HIVEVO_figures/blob/master/src/util.py
def draw_genome(ax, annotations, rows=3, readingframe=True, fs=9):
    from matplotlib.patches import Rectangle
    y1, height, pad = 0, 1, 0.2
    ax.set_ylim([-pad, rows * (height + pad)])
    anno_elements = []
    for name, feature in annotations.iteritems():
        x = [feature.location.nofuzzy_start, feature.location.nofuzzy_end]
        anno_elements.append({
            'name': name,
            'x1': x[0],
            'x2': x[1],
            'width': x[1] - x[0]
        })
    anno_elements.sort(key=lambda x: x['x1'])
    for ai, anno in enumerate(anno_elements):
        if readingframe:
            anno['y1'] = y1 + (height + pad) * (2 - (anno['x1']) % 3)
        else:
            anno['y1'] = y1 + (height + pad) * (ai % rows)
        anno['y2'] = anno['y1'] + height

    for anno in anno_elements:
        r = Rectangle((anno['x1'], anno['y1']),
                      anno['width'],
                      height,
                      facecolor=[0.8] * 3,
                      edgecolor='k',
                      label=anno['name'])

        xt = anno['x1'] + 0.5 * anno['width']
        yt = anno['y1'] + 0.2 * height + height * (anno['width'] < 500)

        ax.add_patch(r)
        ax.text(xt, yt, anno['name'], color='k', fontsize=fs, ha='center')


#移動平均
def running_average_masked(obs, ws, min_valid_fraction=0.95):
    '''
    calculates a running average via convolution, fixing the edges
    obs     --  observations (a masked array)
    ws      --  window size (number of points to average)

    originated from:
    https://github.com/neherlab/HIVEVO_figures/blob/master/src/evolutionary_rates.py
    '''
    #tmp_vals = np.convolve(np.ones(ws, dtype=float), obs*(1-obs.mask), mode='same')
    tmp_vals = np.convolve(np.ones(ws, dtype=float),
                           obs.filled(0),
                           mode='same')

    # if the array is not masked, edges needs to be explictly fixed due to smaller counts
    if len(obs.mask.shape) == 0:
        tmp_valid = ws * np.ones_like(tmp_vals)
        # fix the edges. using mode='same' assumes zeros outside the range
        if ws % 2 == 0:
            tmp_vals[:ws // 2] *= float(ws) / np.arange(ws // 2, ws)
            if ws // 2 > 1:
                tmp_vals[-ws // 2 +
                         1:] *= float(ws) / np.arange(ws - 1, ws // 2, -1.0)
        else:
            tmp_vals[:ws // 2] *= float(ws) / np.arange(ws // 2 + 1, ws)
            tmp_vals[-ws // 2:] *= float(ws) / np.arange(ws, ws // 2, -1.0)

    # if the array is masked, then we get the normalizer from counting the unmasked values
    else:
        tmp_valid = np.convolve(np.ones(ws, dtype=float), (1 - obs.mask),
                                mode='same')

    run_avg = np.ma.array(tmp_vals / tmp_valid)
    run_avg.mask = tmp_valid < ws * min_valid_fraction

    return run_avg
