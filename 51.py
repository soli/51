import random


faces = ['7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
colors = ['C', 'H', 'S', 'D']
values = [7, 8, 0, [-10, 10], 2, 3, 4, [1, 11]]
NCARDS = 5


class Deck():
    def __init__(self):
        self.drawn = 0
        self.cards = list(range(32))
        random.shuffle(self.cards)
        # print(self)

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
        print(self)

    def __str__(self):
        return cards_to_str(self.cards)

    def play(self, heap, new):
        # print(self)
        select, val = self.select(heap)
        card, self.cards[select] = self.cards[select], new
        # print(self)
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
        for i in range(NCARDS):
            print(' ' + str(i + 1), end=' ')
        select = int(input('-> ')) - 1
        val = values[self.cards[select] % 8]
        if isinstance(val, list):
            val = int(input('with which value ' + str(val) + ': '))
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
        print(self)
        print(options)

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
        print(options)
        foo = options.popitem()
        return (foo[1], foo[0] - heap)


class Game():
    def __init__(self):
        self.heap = 0
        self.deck = Deck()
        self.players = [WeakAI(self.deck), HumanPlayer(self.deck)]
        # print(self.deck)

    def play(self):
        current = 0
        while self.deck.drawn < 32 and self.heap < 51:
            self.heap += self.players[current].play(self.heap,
                                                    self.deck.draw(1))
            print(self.heap)
            current = (current + 1) % len(self.players)
        if self.deck.drawn >= 32:
            print('deck is empty, game is a draw')
            return
        last_player = (current - 1) % len(self.players)
        if self.heap > 51:
            print('player ' + str(last_player) + ' has lost')
            return
        print('player ' + str(last_player) + ' has won')
        return


if __name__ == '__main__':
    Game().play()
