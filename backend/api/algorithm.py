def quicksort_routes(routes):
    try:
        if not isinstance(routes, list):
            raise ValueError("Input must be a list")

        if len(routes) <= 1:
            return routes

        pivot = routes[len(routes) // 2]["trip_count"]

        left = []
        middle = []
        right = []

        for route in routes:
            if "trip_count" not in route:
                raise KeyError("trip_count missing in route data")

            if route["trip_count"] > pivot:
                left.append(route)
            elif route["trip_count"] < pivot:
                right.append(route)
            else:
                middle.append(route)

        return quicksort_routes(left) + middle + quicksort_routes(right)

    except Exception as e:
        raise Exception(f"Algorithm error: {str(e)}")
