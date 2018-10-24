

# Basic binary search:
def binary_search(arr, l, r, x):
    # Check base case
    if r >= l:
        mid = l + (r - l) // 2
        # If element is present at the middle itself
        if arr[mid] == x:
            return mid
        # If element is smaller than mid, then it can only be present in left sub-array
        elif arr[mid] > x:
            return binary_search(arr, l, mid - 1, x)
        # Else the element can only be present in right sub-array
        else:
            return binary_search(arr, mid + 1, r, x)
    else:
        return -1


# Emulate C# BinarySearch:
def binary_search_ext(arr, l, r, x):
    i = binary_search(arr, l, r, x)
    if i > 0:
        return i
    else:
        i = 0
        while i < len(arr) - 1:
            if arr[i] > x:
                return i
            i += 1
        return i
