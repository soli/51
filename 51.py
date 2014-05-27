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
    # values that can lead to a 1-move win
    unsafe_values = [50, 49, 48, 47, 44, 43, 41, 40]

    def select(self, heap):
        options = {}
        for select in range(NCARDS):
            val = values[self.cards[select] % 8]
            # FIXME handle duplicates
            if isinstance(val, list):
                options.update([(v + heap, select) for v in val])
            else:
                options[val + heap] = select
        logging.debug('full hand: ' + str(self))
        logging.debug('corresponding options: ' + str(options))

        # can we win?
        if 51 in options:
            return (options[51], 51 - heap)

        # can we avoid to lose?
        nolose = {k:v for k, v in options.items() if k < 52}
        if nolose:
            options = nolose
        # we could have an else to return random immediately but it does not
        # matter that much

        # can we be safe
        safe = {k:v for k, v in options.items() if k not in self.unsafe_values}
        if safe:
            options = safe

        # just be random
        logging.debug('remaining options: ' + str(options))
        foo = options.popitem()
        return (foo[1], foo[0] - heap)


def main():
    # logging.basicConfig(level=logging.DEBUG)

    heap = 0
    deck = Deck()
    players = [WeakAI(deck), HumanPlayer(deck)]
    logging.debug('deck after initial draw: ' + str(deck))

    current = 0
    while deck.drawn < 32 and heap < 51:
        heap += players[current].play(heap, deck.draw(1))
        print(heap)
        current = (current + 1) % len(players)
    if deck.drawn >= 32:
        print('deck is empty, game is a draw')
        return
    last_player = (current - 1) % len(players)
    if heap > 51:
        print('player ' + str(last_player) + ' has lost')
        return
    print('player ' + str(last_player) + ' has won')
    return


if __name__ == '__main__':
    main()
