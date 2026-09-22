from database.database import engine, Base

# Import models so SQLAlchemy registers them before create_all().
from models.ticket import TicketDB
from models.evaluation import InvestigationEvaluationDB
from models.user import UserDB


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Authentication database tables created.")
