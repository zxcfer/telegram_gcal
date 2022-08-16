import logging
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Integer, Text, Boolean   
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError


Base = declarative_base()


class Creds(Base):
    __tablename__ = 'gcal'
    
    state = Column(String(500), nullable=True)
    username = Column(String(500), nullable=True)
    chatId = Column(String(500), nullable=True)
    token = Column(String(500), nullable=True)
    refresh_token = Column(String(500), nullable=True)
    token_uri = Column(String(500), nullable=True)
    client_id = Column(String(500), nullable=True)
    client_secret = Column(String(500), nullable=True)
    
    @classmethod
    def create(cls, db, username):
        try:
            Creds = cls()
            
            creds.state = url
            creds.state = state
            creds.chatId = chatId
            creds.token = token
            creds.refresh_token = refresh_token
            creds.token_uri = token_uri
            creds.client_id = client_id
            creds.client_secret = client_secret            

            session.add(creds)
            session.commit()
            return creds

        except IntegrityError:
            logging.info(f'== WARNING: Existing page!')
            session.rollback()
            creds = session.query(cls).filter_by(username=username).first()
            return creds
           
        except Exception:
            logging.info(f"== WARNING: Can't insert Page!")
            session.rollback()
            raise
