"""Unit tests for station model and database operations."""
from __future__ import annotations

import uuid

import pytest

from piirakka.model.station import (
    Station,
    StationPydantic,
    create_station,
    delete_station,
    get_station,
    list_stations,
    update_station,
)


class TestStationModel:
    """Tests for Station ORM model."""

    def test_station_creation(self, db_session):
        """Test creating a station in the database."""
        station = Station(name="Test Radio", url="http://example.com/stream")
        db_session.add(station)
        db_session.commit()

        assert station.station_id is not None
        assert station.name == "Test Radio"
        assert station.url == "http://example.com/stream"
        assert station.listen_time == 0

    def test_station_to_pydantic(self, db_session):
        """Test converting Station ORM to Pydantic model."""
        station = Station(name="Test Radio", url="http://example.com/stream")
        db_session.add(station)
        db_session.commit()

        pydantic_station = station.to_pydantic()

        assert isinstance(pydantic_station, StationPydantic)
        assert pydantic_station.name == "Test Radio"
        assert pydantic_station.url == "http://example.com/stream"
        assert pydantic_station.station_id == str(station.station_id)


class TestStationOperations:
    """Tests for station CRUD operations."""

    def test_create_station(self, db_session):
        """Test creating a station via the create_station function."""
        station = create_station(db_session, "FM Radio", "http://fm.example.com")

        assert station.name == "FM Radio"
        assert station.url == "http://fm.example.com"

        # Verify it's in the database
        fetched = db_session.query(Station).filter_by(station_id=station.station_id).first()
        assert fetched is not None

    def test_list_stations(self, db_session):
        """Test listing all stations."""
        create_station(db_session, "Station 1", "http://station1.com")
        create_station(db_session, "Station 2", "http://station2.com")

        stations = list_stations(db_session)

        assert len(stations) == 2
        assert any(s.name == "Station 1" for s in stations)
        assert any(s.name == "Station 2" for s in stations)

    def test_get_station(self, db_session):
        """Test retrieving a single station by ID."""
        created = create_station(db_session, "Get Test", "http://gettest.com")

        fetched = get_station(db_session, str(created.station_id))

        assert fetched is not None
        assert fetched.name == "Get Test"

    def test_update_station_name(self, db_session):
        """Test updating station name."""
        station = create_station(db_session, "Old Name", "http://oldname.com")

        updated = update_station(db_session, str(station.station_id), name="New Name", url=None)

        assert updated.name == "New Name"
        assert updated.url == "http://oldname.com"

    def test_update_station_url(self, db_session):
        """Test updating station URL."""
        station = create_station(db_session, "URL Test", "http://oldurl.com")

        updated = update_station(db_session, str(station.station_id), name=None, url="http://newurl.com")

        assert updated.name == "URL Test"
        assert updated.url == "http://newurl.com"

    def test_update_both_fields(self, db_session):
        """Test updating both name and URL."""
        station = create_station(db_session, "Original", "http://original.com")

        updated = update_station(db_session, str(station.station_id), name="Changed", url="http://changed.com")

        assert updated.name == "Changed"
        assert updated.url == "http://changed.com"

    def test_delete_station(self, db_session):
        """Test deleting a station."""
        station = create_station(db_session, "Delete Me", "http://deleteme.com")
        station_id = str(station.station_id)

        success = delete_station(db_session, station_id)

        assert success is True
        fetched = get_station(db_session, station_id)
        assert fetched is None

    def test_delete_nonexistent_station(self, db_session):
        """Test deleting a station that doesn't exist."""
        fake_id = str(uuid.uuid4())

        success = delete_station(db_session, fake_id)

        assert success is False

    def test_update_nonexistent_station(self, db_session):
        """Test updating a station that doesn't exist."""
        fake_id = str(uuid.uuid4())

        result = update_station(db_session, fake_id, name="Should Fail", url=None)

        assert result is False
