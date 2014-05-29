#!/usr/bin/env python3
import random
import logging
import argparse
import sys


faces = ['7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
colors = ['S', 'H', 'D', 'C']
ucolors = ['♠', '♥', '♦', '♣']
values = [7, 8, 0, [-10, 10], 2, 3, 4, [1, 11]]
NCARDS = 5
want_unicode = 0


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
    color = card // 8
    face = card % 8
    if want_unicode == 2:
        # U+1FOA1 is Ace of Spades B1, Hearts...
        base = 0x1F0A7 + 0x10 * color + face
        # Ace is lowest not highest
        if face == 7:
            base -= 13
        return chr(base) + ' '
    if want_unicode == 1:
        return faces[face] + ucolors[color]
    return faces[face] + colors[color]


def cards_to_str(cards):
    return ' '.join(map(card_to_str, cards))


class Player():
    def __init__(self, deck):
        self.cards = deck.draw(NCARDS)
        logging.debug('initial hand: ' + str(self))

    def __str__(self):
        return cards_to_str(self.cards)

    def play(self, heap, last_card, new):
        if last_card is not None:
            self.mark_seen(last_card)
        logging.debug('hand before play: ' + str(self))
        select, val = self.select(heap)
        card, self.cards[select] = self.cards[select], new
        logging.debug('hand after play: ' + str(self))
        self.mark_seen(new)
        print(card_to_str(card), end=' ')   # noqa
        print(heap + val)
        print()
        return heap + val, card

    def select(self, heap):
        raise NotImplementedError('Default player is abstract')

    def mark_seen(self, card):
        pass


class Human(Player):
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


class RandomAI(Player):
    # Random vs. Random
    # about 50-40-10
    def select(self, heap):
        select = random.randrange(NCARDS)
        val = values[self.cards[select] % 8]
        if isinstance(val, list):
            val = random.choice(val)
        return select, val


class WeakAI(Player):
    # WeakAI vs. WeakAI
    # about 30-20-50
    # WeakAI vs. Random
    # about 97-1-2
    def __init__(self, deck):
        super().__init__(deck)
        # values that can lead to a 1-move win
        self.unsafe_values = []
        for v in values:
            if isinstance(v, list):
                self.unsafe_values.extend([51 - val for val in v if val > 0])
            elif v > 0:
                self.unsafe_values.append(51 - v)
        logging.debug('Unsafe values: ' + str(self.unsafe_values))
        # self.unsafe_values.sort(reverse=True)
        # assert self.unsafe_values == [50, 49, 48, 47, 44, 43, 41, 40]

    def build_options(self, heap):
        options = []
        for select in range(NCARDS):
            val = values[self.cards[select] % 8]
            if isinstance(val, list):
                options.extend([(v + heap, select) for v in val])
            else:
                options.append((val + heap, select))
        logging.debug('full hand: ' + str(self))
        logging.debug('corresponding options: ' + str(options))
        return options

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
        # vs. WeakAI
        # - without options.sort()
        # about 12-23-65
        # - without filter_singlevalued()
        # about 35-45-20
        # - without filter_duplicates()
        # about 20-26-54
        options = self.build_options(heap)

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


class StrongAI(WeakAI):
    '''Same as WeakAI but counts seen cards to find new safe plays'''
    # vs. WeakAI
    # about 32-22-46
    def __init__(self, deck):
        super().__init__(deck)
        self.seen = [0] * len(faces)
        for c in self.cards:
            self.mark_seen(c)

    def mark_seen(self, card):
        val = card % 8
        self.seen[val] += 1
        logging.debug('Cards seen: ' + str(self.seen))
        if self.seen[val] == 4:
            self.mark_safe(values[val])

    def mark_safe(self, val):
        if isinstance(val, list):
            for v in val:
                self.mark_safe(v)
        elif val > 0:
            self.unsafe_values.remove(51 - val)


class StrongerAI(StrongAI):
    '''uses seen cards to choose between unsafe plays'''
    # vs. WeakAI
    # about 36-22-42
    # vs. StrongAI
    # about 31-28-41
    def filter_safe(self, options):
        super().filter_safe(options)
        if options[0][0] in self.unsafe_values and len(options) > 1:
            # we have to choose one of the unsafe moves
            reasons = [(k, v, self.seen[value_to_card(51 - k)])
                       for k, v in options]
            logging.debug('options with seen numbers: ' + str(reasons))
            _, _, most = max(reasons, key=lambda x: x[2])
            options.clear()
            options.extend([(k, v) for k, v, s in reasons if s == most])


class DefenseAI(StrongerAI):
    '''a bit more conservative about keeping duplicate 9s and Ts'''
    # vs. WeakAI
    # about 36-16-48
    # vs. StrongerAI
    # about 26-24-50
    def filter_duplicates_offensive(self, options, heap):
        # try to save 9s and Ts as they have strong defensive value
        uniques = list(dict(options).items())
        self.filter_options(options, lambda k, v: (k, v) not in uniques
                            and k not in [heap - 10, heap, heap + 10])

    def select(self, heap):
        '''Same as WeakAI but try to keep 9s and Ts'''
        options = self.build_options(heap)
        self.filter_win(options)
        self.filter_nolose(options)
        self.filter_safe(options)

        self.filter_duplicates_offensive(options, heap)

        self.filter_singlevalued(options, heap)
        options.sort(reverse=True)

        logging.debug('remaining options: ' + str(options))
        return (options[0][1], options[0][0] - heap)


def value_to_card(value):
    for i, v in enumerate(values):
        if isinstance(v, list):
            for vv in v:
                if vv == value:
                    return i
        else:
            if v == value:
                return i


def get_subclasses(cls):
    for c in cls.__subclasses__():
        yield(c.__name__)
        yield from get_subclasses(c)


def game(player1, player2):
    heap = 0
    last_card = None
    deck = Deck()
    # create instances corresponding to the class names given as arguments
    players = [globals()[player1](deck),
               globals()[player2](deck)]
    logging.debug('deck after initial draw: ' + str(deck))

    current = 0
    while deck.drawn < 32 and heap < 51:
        heap, last_card = players[current].play(heap, last_card, deck.draw(1))
        current = (current + 1) % 2
    last_player = (current - 1) % 2 + 1
    if heap == 51:
        print('player ' + str(last_player) + ' has won')
        return 1 - current
    if heap > 51:
        print('player ' + str(last_player) + ' has lost')
        return current
    print('deck is empty, game is a draw')
    return 2


def main():
    # get all known players by introspection
    possible_players = list(get_subclasses(Player))

    with open('README.md') as f:
        long_descr = f.read()
    parser = argparse.ArgumentParser(description=long_descr)
    parser.add_argument('-d', '--debug', help='show (a lot of) debug output',
                        action='store_true')
    parser.add_argument('-n', '--count', type=int, default=1,
                        help='number of games to play (alternating starts)')
    parser.add_argument('-u', '--unicode', type=int, default=1,
                        help='Use ASCII, two unicode chars or a single' +
                        ' unicode char')
    parser.add_argument('players', nargs=2, help='type of players one and two',
                        choices=possible_players)

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if 'Human' in args.players:
        print('Cards\' values:')
        print('7 = 7, 8 = 8, 9 = 0, T = 10 or -10, J = 2, Q = 3, K = 4, ' +
              'A = 1 or 11')
        print()

    global want_unicode
    want_unicode = args.unicode

    won = [0, 0, 0]
    for i in range(args.count):
        j = i % 2
        result = game(args.players[j], args.players[1 - j])
        if result < 2 and j == 1:
            result = 1 - result
        won[result] += 1

    if args.count > 1:
        print(won, file=sys.stderr)


if __name__ == '__main__':
    main()
