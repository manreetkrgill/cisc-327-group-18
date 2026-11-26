from datetime import date


class OverdueAlert:
    """A front-desk notification describing one overdue, unreturned loan.

    Built on demand from a Loan (plus its Book and Member, when they still
    exist), so it is always consistent with the current state of the store.
    """

    def __init__(self, loan, book, member, fine_per_day, today=None):
        today = today or date.today()
        self.loan_id = loan.id
        self.book_id = loan.book_id
        self.book_title = book.title if book else None
        self.member_id = loan.member_id
        self.member_name = member.name if member else None
        self.member_email = member.email if member else None
        self.due_date = loan.due_date
        self.days_overdue = (today - loan.due_date).days
        self.fine_amount = round(self.days_overdue * fine_per_day, 2)

    def message(self):
        who = self.member_name or f"Member #{self.member_id}"
        what = f"'{self.book_title}'" if self.book_title else f"book #{self.book_id}"
        return (
            f"{who} has {what} overdue by {self.days_overdue} day(s); "
            f"fine owed ${self.fine_amount:.2f}"
        )

    def to_dict(self):
        return {
            "loan_id": self.loan_id,
            "book_id": self.book_id,
            "book_title": self.book_title,
            "member_id": self.member_id,
            "member_name": self.member_name,
            "member_email": self.member_email,
            "due_date": self.due_date.isoformat(),
            "days_overdue": self.days_overdue,
            "fine_amount": self.fine_amount,
            "message": self.message(),
        }
