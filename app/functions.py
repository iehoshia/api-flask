def get_product(number):
    choises = {
        1: 2,
        2: 6,
        3: 1,
        4: 4,
        5: 7,
        6: 9,
        7: 11,
        8: 8,
        9: 10,
    }
    return choises.get(number, 2)

#print get_product(2)