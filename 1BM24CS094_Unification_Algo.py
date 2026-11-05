def occurs_in(var, expr):
    if var == expr:
        return True
    if isinstance(expr, list):
        return any(occurs_in(var, sub) for sub in expr)
    return False

def apply_substitution(expr, subst):
    if subst is None or subst == "NIL":
        return expr
    if isinstance(expr, list):
        return [apply_substitution(item, subst) for item in expr]
    if expr in subst:
        return apply_substitution(subst[expr], subst)
    return expr

def unify(psi1, psi2, variables):
    if isinstance(psi1, str) and psi1 in variables or isinstance(psi2, str) and psi2 in variables:
        if psi1 == psi2:
            return "NIL"
        elif isinstance(psi1, str) and psi1 in variables:
            if occurs_in(psi1, psi2):
                return "FAILURE"
            else:
                return {psi1: psi2}
        elif isinstance(psi2, str) and psi2 in variables:
            if occurs_in(psi2, psi1):
                return "FAILURE"
            else:
                return {psi2: psi1}

    if not isinstance(psi1, list) or not isinstance(psi2, list):
        if psi1 != psi2:
            return "FAILURE"
        return "NIL"

    if len(psi1) != len(psi2):
        return "FAILURE"

    if psi1[0] != psi2[0]:
        return "FAILURE"

    subst = "NIL"

    for i in range(1, len(psi1)):
        current_psi1 = apply_substitution(psi1[i], subst)
        current_psi2 = apply_substitution(psi2[i], subst)

        s = unify(current_psi1, current_psi2, variables)

        if s == "FAILURE":
            return "FAILURE"

        if s != "NIL":
            if subst == "NIL":
                subst = {}
            for k in subst:
                subst[k] = apply_substitution(subst[k], s)
            for k in s:
                subst[k] = s[k]

    return subst

var_set = {"X", "y", "z"}

expr1 = ["p" ,"b", "X", ["f", ["g","z"]]]
expr2 = ["p" ,"z", ["f", "y"], ["f", "y"]]

print("Expressions:", expr1, "and", expr2)
print("Result:", unify(expr1, expr2, var_set))

var_set = {"x", "y", "z"}
expr1 = ["P", "A", "B", "B"]
expr2 = ["P", "x", "y", "z"]

print("Result A:", unify(expr1, expr2, var_set))

var_set = {"x", "y"}
expr1 = ["Q", "y", ["G", "A", "B"]]
expr2 = ["Q", ["G", "x", "x"], "y"]

print("Result B:", unify(expr1, expr2, var_set))

var_set = {"x", "y"}
expr1 = ["Older", ["Father", "y"], "y"]
expr2 = ["Older", ["Father", "x"], "John"]

print("Result C:", unify(expr1, expr2, var_set))

var_set = {"x", "y"}
expr1 = ["Knows", ["Father", "y"], "y"]
expr2 = ["Knows", "x", "x"]

print("Result D:", unify(expr1, expr2, var_set))