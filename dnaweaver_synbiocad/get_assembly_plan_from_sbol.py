import sbol2 as sbol
from collections import OrderedDict

MIN_PART_LENGTH = 179
MAX_PART_LENGTH = 1760
MAX_SUB_PARTS = 3


def get_dna_sequence(component: sbol.ComponentDefinition, sbol_doc: sbol.Document):
    for seq_identity in component.sequences:
        try:
            seq = sbol_doc.getSequence(seq_identity)
            if seq.encoding == sbol.SBOL_ENCODING_IUPAC:
                return seq.elements.upper()
        except sbol.SBOLError:
            pass

    return ''


def refactor_construct_parts(parts_per_construct: list, part_sequences: dict):
    refactored_parts_per_construct = []
    refactored_part_sequences = {}

    for construct, construct_parts in parts_per_construct:
        refactored_construct_parts = []

        part_refactor = []
        seq_refactor = []
        refactor_length = 0

        for part in construct_parts:
            part_seq = part_sequences[part]

            if (refactor_length + len(part_seq) > MAX_PART_LENGTH or (len(part_refactor) >= MAX_SUB_PARTS
                                                                      and refactor_length > MIN_PART_LENGTH)):
                refactored_part = '_'.join(part_refactor)
                refactored_construct_parts.append(refactored_part)
                if refactored_part not in refactored_part_sequences:
                    refactored_part_sequences[refactored_part] = ''.join(seq_refactor)

                part_refactor = [part]
                seq_refactor = [part_seq]
                refactor_length = len(part_seq)
            else:
                part_refactor.append(part)
                seq_refactor.append(part_seq)
                refactor_length = refactor_length + len(part_seq)

        if len(part_refactor) > 0:
            refactored_part = '_'.join(part_refactor)
            refactored_construct_parts.append(refactored_part)
            if refactored_part not in refactored_part_sequences:
                refactored_part_sequences[refactored_part] = ''.join(seq_refactor)

        refactored_parts_per_construct.append((construct, refactored_construct_parts))

    return (refactored_parts_per_construct, refactored_part_sequences)


def get_assembly_plan_from_sbol(sbol_doc=None, path=None):
    """Extract an assembly plan from sbol

    :param sbol_doc: A PySBOL Document() containing the designs and parts sequences. A path to a SBOL .xml file can be provided instead.
    :param path: A path to a SBOL .xml file

    :type sbol_doc: sbol.Document
    :type path: str
    
    :rtype: tuple
    :return: Return a tuple with part_sequences, parts_per_construct, construct_sequences, and construct_topologies
      Assembly plan data:
      - part_sequences is of the form ``{part_id: "ATTTGTGTGC..."}``,
      - parts_per_constructs is of the form ``{construct_id: [part_id_1,...]}``,
      - construct_sequences is of the form ``{construct_id: "ATGCCC..."}``,
      - construct_topologies is of the form ``{construct_id: "linear"}``.
    """
    if path is not None:
        sbol_doc = sbol.Document()
        sbol_doc.read(path)

    parts_per_construct = []
    construct_sequences = {}
    construct_topologies = {}
    for component in sbol_doc.componentDefinitions:
        try:
            sub_components = component.getPrimaryStructure()
        except ValueError:
            sub_components = []
        if len(sub_components) > 0:
            parts_per_construct.append((component.displayId, [c.displayId for c in sub_components]))

            construct_seq = get_dna_sequence(component, sbol_doc)
            if len(construct_seq) > 0:
                construct_sequences[component.displayId] = construct_seq

            if sbol.SO_CIRCULAR in component.types:
                construct_topologies[component.displayId] = 'circular'
            else:
                construct_topologies[component.displayId] = 'linear'

    parts = set()
    for construct, construct_parts in parts_per_construct:
        parts.update(construct_parts)

    parts_per_construct = [(construct, construct_parts)
                           for construct, construct_parts in parts_per_construct
                           if construct not in parts]

    construct_sequences = {construct: construct_sequences[construct]
                           for construct in construct_sequences
                           if construct not in parts}

    parts = set()
    for construct, construct_parts in parts_per_construct:
        parts.update(construct_parts)

    part_sequences = {}
    for part in parts:
        try:
            component = sbol_doc.getComponentDefinition(part)
            
            part_seq = get_dna_sequence(component, sbol_doc)

            if len(part_seq) > 0:
                part_sequences[component.displayId] = part_seq
        except sbol.SBOLError:
            pass

    parts_per_construct, part_sequences = refactor_construct_parts(parts_per_construct, part_sequences)

    for construct, construct_parts in parts_per_construct:
        if construct not in construct_sequences:
            construct_sequences[construct] = "".join([part_sequences[part] for part in construct_parts])

    sequence_per_construct = [
        (construct, construct_sequences[construct])
        for construct in construct_sequences
    ]

    parts_per_construct = OrderedDict(parts_per_construct)
    construct_sequences = OrderedDict(sequence_per_construct)
    return (part_sequences, parts_per_construct, construct_sequences, construct_topologies)
