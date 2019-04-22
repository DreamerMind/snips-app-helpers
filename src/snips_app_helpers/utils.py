from decimal import Decimal


class BaseObj(object):
    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()


def iter_file_in_tree(base_dir):
    for path in base_dir.iterdir():
        if path.is_dir():
            yield from iter_file_in_tree(path)
        if path.is_file():
            yield path


def iter_lines_in_tree(base_dir):
    for filepath in iter_file_in_tree(base_dir):
        with filepath.open("rb") as fh:
            for line_idx, line in enumerate(fh):
                yield filepath, line_idx, str(line)


def score_text_sequence(text):
    """
    notes:
        magic number come from https://stackoverflow.com/questions/5924105/how-many-characters-can-be-mapped-with-unicode
        unicode contain currently 128237 unique char in v9.0

        numbers of characters become swiftly a problem with this formulation,
        because it ends up trucating the decimal stored due to summation

        this shouldn't be a problem in our formulation as the text rarely
        have mutual start sequence further than 20 chars

    """
    score = Decimal(0)
    num_utf8_char = Decimal(128237)
    for idx, char in enumerate(text):
        score += Decimal(ord(char)) / num_utf8_char / Decimal(2 ** idx)
    return 1 - score


def group_set_subsets_of_others(given_sets):
    sets_size_ordered = list(
        reversed(
            sorted(
                list(given_sets),
                # must enforce scale under 1
                # in alpha orderding
                key=lambda x: len(x) + score_text_sequence(str(x)),
            )
        )
    )
    consumed_sets = set()
    groups = []
    # longuest first
    for given_set in sets_size_ordered:
        if given_set in consumed_sets:
            continue

        group = []
        consumed_sets.add(given_set)

        for given_set2 in sets_size_ordered:
            if given_set2 in consumed_sets:
                continue
            if given_set.issuperset(given_set2):
                group.append(given_set2)
                consumed_sets.add(given_set2)
            # add first set
        groups.append((given_set, frozenset(group)))
    return set(groups)


def frozen_set_to_list(item):
    if isinstance(item, (frozenset, set)):
        return frozen_set_to_list(list(item))
    elif isinstance(item, dict):
        return {k: frozen_set_to_list(v) for k, v in item.items()}
    elif isinstance(item, list):
        return [frozen_set_to_list(it) for it in item]
    else:
        return item
