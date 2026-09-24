from locations.geo_functions import get_distance


def find_suited_restaurants(order, products_by_restaurant, restaurants):
    order_product_ids = order.get_product_ids()
    return [
        restaurants[restaurant_id]
        for restaurant_id, product_ids in products_by_restaurant.items()
        if order_product_ids <= product_ids
    ]


def measure_distances(order_restaurants, order_coordinates, coordinates_by_address):
    restaurants_with_distance = [
        (
            restaurant,
            get_distance(order_coordinates, coordinates_by_address[restaurant.address]),
        )
        for restaurant in order_restaurants
    ]
    return sorted(
        restaurants_with_distance,
        key=lambda item: (
            item[1]
            if item[1] is not None
            else float('inf')
    ))

