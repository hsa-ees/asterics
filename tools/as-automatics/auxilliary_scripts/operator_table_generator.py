import copy

# Generation function
def generate_add_sub_mapping(max_add_sub: int, bitcount: int) -> tuple:

    operators_p = dict()
    operators_n = dict()
    numbers = list()
    for x in range(2 ** bitcount + 1):
        operators_p[x] = []
        operators_n[x] = []
        if x == 0:
            numbers.append(True)
        else:
            numbers.append(False)

    for x in range(bitcount + 1):
        num = 2 ** x
        numbers[num] = True
        operators_p[num].append(num)

    def iterate_add_sub(bitcount):
        tempnums = copy.copy(numbers)
        maxval = 2 ** bitcount
        for num in range(len(numbers)):
            if not tempnums[num]:
                continue
            for x in range(bitcount):
                offset = 2 ** x
                add = num + offset
                sub = num - offset
                if 0 <= add <= maxval:
                    if not numbers[add]:
                        numbers[add] = True
                        operators_p[add] = copy.copy(operators_p[num])
                        operators_p[add].append(offset)
                        operators_n[add] = copy.copy(operators_n[num])
                if 0 <= sub <= maxval:
                    if not numbers[sub]:
                        numbers[sub] = True
                        operators_p[sub] = copy.copy(operators_p[num])
                        operators_n[sub] = copy.copy(operators_n[num])
                        operators_n[sub].append(offset)

    for _ in range(max_add_sub):
        iterate_add_sub(bitcount)
    return (numbers, operators_p, operators_n)


# Configuration
bitcount = 8
addsub = 4
# Report configuration
print_possible = False
print_not_possible = False
print_hdl = True
print_negative_hdl = False

# Generate
print(f"Using a maximum of {addsub} additions/subtractions:")
numbers, operators_p, operators_n = generate_add_sub_mapping(addsub, bitcount)


# Reporting
possible = numbers.count(True) - 1
npossible = numbers.count(False)
total = 2 ** bitcount
print(
    f"{(possible / total)*100:.2f}% of numbers possible ({possible}), {npossible} not representable."
)

if print_possible or print_not_possible:
    print("Number to operations mapping:")
    for x in range(2 ** bitcount):
        factors = f"Possible using factors +{operators_p[x]} -{operators_n[x]}"
        possible = numbers[x]
        if print_possible and possible or print_not_possible and not possible:
            print(f"{x} -> {'Not possible.' if not numbers[x] else factors}")

if print_negative_hdl:
    for x in range(2 ** bitcount):
        pop = 0
        nop = 0
        pop = sum(operators_p[x])
        nop = sum(operators_n[x])
        str_pop = f'"{pop:09b}"'
        str_nop = f'"{nop:09b}"'
        factors = f"({str_nop}, {str_pop})"
        factors_str = f": +{sorted(operators_n[x])} -{sorted(operators_p[x])}"
        print(
            f"{factors},  -- {'-' if x > 0 else ''}{x} {'-X-' if not numbers[x] else factors_str}"
        )

if print_hdl:
    for x in range(2 ** bitcount):
        pop = 0
        nop = 0
        pop = sum(operators_p[x])
        nop = sum(operators_n[x])
        str_pop = f'"{pop:09b}"'
        str_nop = f'"{nop:09b}"'
        factors = f"({str_pop}, {str_nop})"
        factors_str = f": +{sorted(operators_p[x])} -{sorted(operators_n[x])}"
        print(f"{factors},  -- {x} {'-X-' if not numbers[x] else factors_str}")
