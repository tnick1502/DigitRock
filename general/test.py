

A = {
    "x": {
        "a": 3
    },
    "y": {
        "a": 1
    }
}
sort_key = "a"
ss = dict(sorted(A.items(), key=lambda x: A[x[0]][sort_key]))
print(ss)