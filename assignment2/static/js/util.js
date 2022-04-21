function binarySearch(array, pred) {
    let lo = -1, hi = array.length
    while (1 + lo < hi) {
        const mi = lo + ((hi - lo) >> 1)
        if (pred(array[mi])) {
            hi = mi
        } else {
            lo = mi
        }
    }
    return hi
}

function lowerBound(array, item) {
    return binarySearch(array, j => item <= j[1])
}

function upperBound(array, item) {
    return binarySearch(array, j => item < j[1])
}

export {binarySearch, upperBound, lowerBound}
