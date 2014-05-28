#!/usr/bin/env python3
import random
import logging


faces = ['7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
colors = ['C', 'H', 'S', 'D']
values = [7, 8, 0, [-10, 10], 2, 3, 4, [1, 11]]
NCARDS = 5


class Deck():
    def __init__(self):
        self.drawn = 0
        self.cards = list(range(32))
        random.shuffle(self.cards)
        logging.debug('deck:\n' + str(self))

    def __str__(self):
        return ' ' + cards_to_str(self.cards) + '\n' + \
            (3 * self.drawn) * ' ' + '^'

    def draw(self, n=1):
        if n + self.drawn > 32:
            raise Exception('the deck is empty, cannot draw')
        index = self.drawn
        self.drawn += n
        if n > 1:
            return self.cards[index:self.drawn]
        return self.cards[index]


def card_to_str(card):
    return faces[card % 8] + colors[card // 8]


def cards_to_str(cards):
    return ' '.join(map(card_to_str, cards))


class Player():
    def __init__(self, deck):
        self.cards = deck.draw(NCARDS)
        logging.debug('initial hand: ' + str(self))

    def __str__(self):
        return cards_to_str(self.cards)

    def play(self, heap, new):
        logging.debug('hand before play: ' + str(self))
        select, val = self.select(heap)
        card, self.cards[select] = self.cards[select], new
        logging.debug('hand after play: ' + str(self))
        print(card_to_str(card), end=' ')   # noqa
        return val

    def select(self, heap):
        raise NotImplementedError('Default player is abstract')


class RandomPlayer(Player):
    def select(self, heap):
        select = random.randrange(NCARDS)
        val = values[self.cards[select] % 8]
        if isinstance(val, list):
            val = random.choice(val)
        return select, val


class HumanPlayer(Player):
    def select(self, heap):
        print(self)
        select = -1
        while select < 0 or select > 4:
            for i in range(NCARDS):
                print(' ' + str(i + 1), end=' ')
            try:
                select = int(input('-> ')) - 1
            except ValueError:
                select = -1
        val = values[self.cards[select] % 8]
        if isinstance(val, list):
            v = -1
            while v not in val:
                try:
                    v = int(input('with which value ' + str(val) + ': '))
                except ValueError:
                    v = -1
            val = v
        return select, val


class WeakAI(Player):
    def __init__(self, deck):
        super().__init__(deck)
        # values that can lead to a 1-move win
        self.unsafe_values = []
        for v in values:
            if isinstance(v, list):
                self.unsafe_values.extend([51 - val for val in v if val > 0])
            elif v > 0:
                self.unsafe_values.append(51 - v)
        self.unsafe_values.sort(reverse=True)
        logging.debug('Unsafe values: ' + str(self.unsafe_values))
        # assert self.unsafe_values == [50, 49, 48, 47, 44, 43, 41, 40]

    def filter_options(self, options, func):
        filtered = [(k, v) for k, v in options if func(k, v)]
        if filtered:
            # options = filtered
            options.clear()
            options.extend(filtered)

    def filter_win(self, options):
        self.filter_options(options, lambda k, v: k == 51)

    def filter_nolose(self, options):
        self.filter_options(options, lambda k, v: k < 52)

    def filter_safe(self, options):
        self.filter_options(options, lambda k, v: k not in self.unsafe_values)

    def filter_duplicates(self, options):
        uniques = list(dict(options).items())
        self.filter_options(options, lambda k, v: (k, v) not in uniques)

    def filter_singlevalued(self, options, heap):
        # FIXME should be computed directly from options not using heap
        single_vals = [v + heap for v in values if isinstance(v, int)]
        self.filter_options(options, lambda k, v: k in single_vals)

    def select(self, heap):
        '''Implements a 1-ply lookahead

        The evaluation function is defined by lexical ordering:
        - move can win
        - move can avoid to lose
        - move is safe (opponent cannot win in 1 move)
        - twice or more the same card
        - cards with a single value
        - cards with highest value

        This ordering is implemented by successive filtering.'''
        options = []
        for select in range(NCARDS):
            val = values[self.cards[select] % 8]
            if isinstance(val, list):
                options.extend([(v + heap, select) for v in val])
            else:
                options.append((val + heap, select))
        logging.debug('full hand: ' + str(self))
        logging.debug('corresponding options: ' + str(options))

        # can we win?
        self.filter_win(options)
        # we could return here...

        # can we avoid to lose?
        self.filter_nolose(options)
        # we could have an else to return random immediately but it does not
        # matter that much

        # can we be safe
        self.filter_safe(options)

        # are there duplicates (they do not bring anything)
        self.filter_duplicates(options)

        # are there single value cards (less useful than double ones)
        self.filter_singlevalued(options, heap)

        # just take highest
        options.sort(reverse=True)

        logging.debug('remaining options: ' + str(options))
        return (options[0][1], options[0][0] - heap)


def main():
    # logging.basicConfig(level=logging.DEBUG)

    print('Cards\' values:')
    print(
        '7 = 7, 8 = 8, 9 = 0, T = 10 or -10, J = 2, Q = 3, K = 4, A = 1 or 11')
    print()

    heap = 0
    deck = Deck()
    players = [WeakAI(deck), HumanPlayer(deck)]
    logging.debug('deck after initial draw: ' + str(deck))

    current = 0
    while deck.drawn < 32 and heap < 51:
        heap += players[current].play(heap, deck.draw(1))
        print(heap)
        print()
        current = (current + 1) % len(players)
    if deck.drawn >= 32:
        print('deck is empty, game is a draw')
        return 0
    last_player = (current - 1) % len(players) + 1
    if heap > 51:
        print('player ' + str(last_player) + ' has lost')
        return current
    print('player ' + str(last_player) + ' has won')
    return last_player


if __name__ == '__main__':
    main()
