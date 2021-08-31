
def round_sigma_3(sigma_3):
    integer = sigma_3 // 5
    remains = sigma_3 % 5
    return integer * 5 if remains < 2.5 else integer * 5 + 5


print(round_sigma_3(303))