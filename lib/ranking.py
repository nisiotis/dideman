# -*- coding: utf-8 -*-

RANKS = list(zip(['ΣΤ'] * 3 + ['Ε'] * 6 + ['Δ'] * 6 + ['Γ'] * 6 + ['Β'] * 27,
            [0, 0, 0,
             0, 0, 1, 1, 2, 2,
             0, 0, 1, 1, 2, 2,
             0, 0, 1, 1, 2, 2,
             0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8]))


def next_index(rank):
    try:
        index = RANKS.index(rank)
        return next(RANKS.index((r, mk))
                    for r, mk in RANKS[index:]
                    if (r, mk) != rank)
    except ValueError as e:
        return 0
