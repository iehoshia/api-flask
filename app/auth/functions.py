def get_product(number):
    choises = {
        1: 2,
        2: 3,
        3: 4,
        5: 6, 
        7: 8, 
        8: 9,
        9: 10,
    }
    return choises.get(number, 2)

#print get_product(2) 
