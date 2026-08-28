"""
THABZO EVENTS - Quote Service
"""
from thabzo.models import Service, Inquiry


class QuoteService:
    """Service for calculating quotes and estimates"""

    BASE_RATES = {
        'wedding': 5000,
        'birthday': 2500,
        'corporate': 8000,
        'baby-shower': 2000,
        'engagement': 3000,
        'anniversary': 3500,
        'other': 3000
    }

    COMPLEXITY_FACTORS = {
        'simple': 1.0,
        'medium': 1.5,
        'complex': 2.0
    }

    @classmethod
    def estimate_price(cls, event_type, guest_count=None, complexity='medium',
                       add_ons=None):
        """Estimate price based on event parameters"""
        base_price = cls.BASE_RATES.get(event_type, 3000)

        factor = cls.COMPLEXITY_FACTORS.get(complexity, 1.5)
        price = base_price * factor

        if guest_count and guest_count > 50:
            extra = (guest_count - 50) // 50
            price += price * (0.05 * extra)

        if add_ons:
            add_on_prices = {
                'floral': 1500,
                'lighting': 2000,
                'furniture': 2500,
                'backdrop': 1000,
                'stationery': 800
            }
            for add_on in add_ons:
                price += add_on_prices.get(add_on, 500)

        return round(price, 2)

    @classmethod
    def get_price_range(cls, event_type):
        """Get price range for an event type"""
        base = cls.BASE_RATES.get(event_type, 3000)
        return (base, base * 3)

    @classmethod
    def generate_quote_response(cls, inquiry):
        """Generate a quote response for an inquiry"""
        estimate = cls.estimate_price(inquiry.event_type)

        return {
            'client_name': inquiry.name,
            'event_type': inquiry.get_event_type_display(),
            'estimate': estimate,
            'price_range': cls.get_price_range(inquiry.event_type),
            'note': 'This is an estimate. Final price may vary based on specific requirements.'
        }


def get_quick_estimate(event_type, guest_count=None):
    """Quick estimate function for public use"""
    estimate = QuoteService.estimate_price(event_type, guest_count)
    if estimate:
        return f'R{estimate:,.2f}'.replace('.00', '')
    return 'Contact us for a quote'