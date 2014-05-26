import random


values = ['7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
colors = ['C', 'H', 'S', 'D']


class Deck():
    def __init__(self):
        self.drawn = 0
        self.cards = list(range(32))
        random.shuffle(self.cards)
        print(self)

    def __str__(self):
        return ' ' + cards_to_str(self.cards) + '\n' + \
            (3 * self.drawn) * ' ' + '^'

    def draw(self, n):
        if n + self.drawn > 32:
            raise Exception('the deck is now empty, the game is drawn')
        index = self.drawn
        self.drawn += n
        return self.cards[index:self.drawn]


def card_to_str(card):
    return values[card % 8] + colors[card // 8]


def cards_to_str(cards):
    return ' '.join(map(card_to_str, cards))


class Player():
    def __init__(self, deck):
        self.cards = deck.draw(5)
        print(self)

    def __str__(self):
        return cards_to_str(self.cards)


def main():
    deck = Deck()
    Player(deck)
    Player(deck)
    print(deck)


if __name__ == '__main__':
    main()
