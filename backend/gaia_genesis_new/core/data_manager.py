from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
from datetime import date

# Assuming models and schemas are structured as previously discussed
from backend.gaia_genesis_new.core.database_models import Reservoir, Well, ProductionData, PVTData, Simulation
from backend.gaia_genesis_new.api_v1 import schemas as api_schemas # Use an alias for clarity
from backend.gaia_genesis_new.logger import logger


class DataManager:
    def __init__(self, db: Session):
        self.db = db

    # ----- Reservoir Operations -----
    def create_reservoir(self, reservoir: api_schemas.ReservoirCreate) -> Optional[Reservoir]:
        """Create a new reservoir"""
        try:
            db_reservoir = Reservoir(**reservoir.dict())
            self.db.add(db_reservoir)
            self.db.commit()
            self.db.refresh(db_reservoir)
            logger.info(f"Reservoir '{db_reservoir.name}' created with ID {db_reservoir.id}.")
            return db_reservoir
        except SQLAlchemyError as e:
            logger.error(f"Error creating reservoir '{reservoir.name}': {str(e)}")
            self.db.rollback()
            return None

    def get_reservoir(self, reservoir_id: int) -> Optional[Reservoir]:
        """Get a reservoir by ID"""
        return self.db.query(Reservoir).filter(Reservoir.id == reservoir_id).first()

    def get_reservoir_by_name(self, name: str) -> Optional[Reservoir]:
        """Get a reservoir by name"""
        return self.db.query(Reservoir).filter(Reservoir.name == name).first()

    def get_all_reservoirs(self, skip: int = 0, limit: int = 100) -> List[Reservoir]:
        """Get all reservoirs with pagination"""
        return self.db.query(Reservoir).offset(skip).limit(limit).all()

    def update_reservoir(self, reservoir_id: int, reservoir_update: api_schemas.ReservoirUpdate) -> Optional[Reservoir]:
        """Update reservoir information"""
        db_reservoir = self.get_reservoir(reservoir_id)
        if not db_reservoir:
            logger.warning(f"Reservoir with ID {reservoir_id} not found for update.")
            return None

        update_data = reservoir_update.dict(exclude_unset=True)
        try:
            for key, value in update_data.items():
                setattr(db_reservoir, key, value)
            self.db.commit()
            self.db.refresh(db_reservoir)
            logger.info(f"Reservoir ID {reservoir_id} updated.")
            return db_reservoir
        except SQLAlchemyError as e:
            logger.error(f"Error updating reservoir ID {reservoir_id}: {str(e)}")
            self.db.rollback()
            return None

    def delete_reservoir(self, reservoir_id: int) -> bool:
        """Delete a reservoir and its related wells/simulations (due to cascade)"""
        db_reservoir = self.get_reservoir(reservoir_id)
        if not db_reservoir:
            logger.warning(f"Reservoir with ID {reservoir_id} not found for deletion.")
            return False
        try:
            self.db.delete(db_reservoir)
            self.db.commit()
            logger.info(f"Reservoir ID {reservoir_id} and its related data deleted.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting reservoir ID {reservoir_id}: {str(e)}")
            self.db.rollback()
            return False

    # ----- Well Operations -----
    def create_well(self, well: api_schemas.WellCreate) -> Optional[Well]:
        """Create a new well"""
        # Verify reservoir exists
        if not self.get_reservoir(well.reservoir_id):
            logger.error(f"Reservoir {well.reservoir_id} not found. Cannot create well '{well.name}'.")
            return None
        try:
            db_well = Well(**well.dict())
            self.db.add(db_well)
            self.db.commit()
            self.db.refresh(db_well)
            logger.info(f"Well '{db_well.name}' created with ID {db_well.id} in reservoir {db_well.reservoir_id}.")
            return db_well
        except SQLAlchemyError as e:
            logger.error(f"Error creating well '{well.name}': {str(e)}")
            self.db.rollback()
            return None

    def get_well(self, well_id: int) -> Optional[Well]:
        """Get a well by ID"""
        return self.db.query(Well).filter(Well.id == well_id).first()

    def get_wells_by_reservoir(self, reservoir_id: int, skip: int = 0, limit: int = 100) -> List[Well]:
        """Get all wells in a reservoir with pagination"""
        return self.db.query(Well).filter(Well.reservoir_id == reservoir_id).offset(skip).limit(limit).all()

    def update_well(self, well_id: int, well_update: api_schemas.WellUpdate) -> Optional[Well]:
        """Update well information"""
        db_well = self.get_well(well_id)
        if not db_well:
            logger.warning(f"Well with ID {well_id} not found for update.")
            return None

        update_data = well_update.dict(exclude_unset=True)
        # If changing reservoir, verify new reservoir exists
        if 'reservoir_id' in update_data and update_data['reservoir_id'] is not None:
            if not self.get_reservoir(update_data['reservoir_id']):
                logger.error(f"Target reservoir {update_data['reservoir_id']} not found for well update.")
                return None
        try:
            for key, value in update_data.items():
                setattr(db_well, key, value)
            self.db.commit()
            self.db.refresh(db_well)
            logger.info(f"Well ID {well_id} updated.")
            return db_well
        except SQLAlchemyError as e:
            logger.error(f"Error updating well ID {well_id}: {str(e)}")
            self.db.rollback()
            return None

    def delete_well(self, well_id: int) -> bool:
        """Delete a well and its related data (due to cascade)"""
        db_well = self.get_well(well_id)
        if not db_well:
            logger.warning(f"Well with ID {well_id} not found for deletion.")
            return False
        try:
            self.db.delete(db_well)
            self.db.commit()
            logger.info(f"Well ID {well_id} and its related data deleted.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting well ID {well_id}: {str(e)}")
            self.db.rollback()
            return False

    # ----- Production Data Operations -----
    def add_production_data(self, production_data: api_schemas.ProductionDataCreate) -> Optional[ProductionData]:
        """Add production data for a well"""
        if not self.get_well(production_data.well_id):
            logger.error(f"Well {production_data.well_id} not found. Cannot add production data.")
            return None
        try:
            db_production = ProductionData(**production_data.dict())
            self.db.add(db_production)
            self.db.commit()
            self.db.refresh(db_production)
            # logger.info(f"Production data added for well ID {db_production.well_id} on date {db_production.date}.")
            return db_production
        except SQLAlchemyError as e:
            logger.error(f"Error adding production data for well ID {production_data.well_id}: {str(e)}")
            self.db.rollback()
            return None

    def get_production_data_for_well(self, well_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None, skip: int = 0, limit: int = 1000) -> List[ProductionData]:
        """Get production data for a well within a date range, with pagination"""
        query = self.db.query(ProductionData).filter(ProductionData.well_id == well_id)
        if start_date:
            query = query.filter(ProductionData.date >= start_date)
        if end_date:
            query = query.filter(ProductionData.date <= end_date)
        return query.order_by(ProductionData.date.asc()).offset(skip).limit(limit).all()

    def delete_production_data(self, production_id: int) -> bool:
        """Delete specific production data entry"""
        db_production = self.db.query(ProductionData).filter(ProductionData.id == production_id).first()
        if not db_production:
            logger.warning(f"Production data with ID {production_id} not found for deletion.")
            return False
        try:
            self.db.delete(db_production)
            self.db.commit()
            logger.info(f"Production data ID {production_id} deleted.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting production data ID {production_id}: {str(e)}")
            self.db.rollback()
            return False

    def batch_create_production_data(self, production_records: List[api_schemas.ProductionDataCreate]) -> int:
        """Bulk insert production data records"""
        # Consider validating well_ids first if performance allows
        count = 0
        try:
            # Can't use self.db.bulk_save_objects directly if we need to return created objects with IDs
            # For simple insert and count:
            self.db.execute(ProductionData.__table__.insert(), [record.dict() for record in production_records])
            # Or iterate and add if refresh is needed, but that's less "batchy"
            # For now, let's assume simple insert is enough.
            self.db.commit()
            count = len(production_records)
            logger.info(f"Batch created {count} production records.")
        except SQLAlchemyError as e:
            logger.error(f"Error in batch production data creation: {str(e)}")
            self.db.rollback()
            return 0
        return count

    # ----- PVT Data Operations -----
    def add_pvt_data(self, pvt_data: api_schemas.PVTDataCreate) -> Optional[PVTData]:
        """Add PVT data for a well"""
        if not self.get_well(pvt_data.well_id):
            logger.error(f"Well {pvt_data.well_id} not found. Cannot add PVT data.")
            return None
        try:
            db_pvt = PVTData(**pvt_data.dict())
            self.db.add(db_pvt)
            self.db.commit()
            self.db.refresh(db_pvt)
            # logger.info(f"PVT data added for well ID {db_pvt.well_id} at pressure {db_pvt.pressure}.")
            return db_pvt
        except SQLAlchemyError as e:
            logger.error(f"Error adding PVT data for well ID {pvt_data.well_id}: {str(e)}")
            self.db.rollback()
            return None

    def get_pvt_data_for_well(self, well_id: int, skip: int = 0, limit: int = 100) -> List[PVTData]:
        """Get all PVT data for a well with pagination"""
        return self.db.query(PVTData).filter(PVTData.well_id == well_id).order_by(PVTData.pressure.asc()).offset(skip).limit(limit).all()

    # ----- Simulation Operations -----
    def create_simulation(self, simulation: api_schemas.SimulationCreate) -> Optional[Simulation]:
        """Create a new simulation entry"""
        if not self.get_reservoir(simulation.reservoir_id):
            logger.error(f"Reservoir {simulation.reservoir_id} not found. Cannot create simulation '{simulation.name}'.")
            return None
        try:
            db_simulation = Simulation(**simulation.dict())
            self.db.add(db_simulation)
            self.db.commit()
            self.db.refresh(db_simulation)
            logger.info(f"Simulation '{db_simulation.name}' created with ID {db_simulation.id} for reservoir {db_simulation.reservoir_id}.")
            return db_simulation
        except SQLAlchemyError as e:
            logger.error(f"Error creating simulation '{simulation.name}': {str(e)}")
            self.db.rollback()
            return None

    def get_simulation(self, simulation_id: int) -> Optional[Simulation]:
        """Get simulation by ID"""
        return self.db.query(Simulation).filter(Simulation.id == simulation_id).first()

    def update_simulation_status(self, simulation_id: int, status: str, results_path: Optional[str] = None) -> Optional[Simulation]:
        """Update simulation status and optionally results path"""
        db_simulation = self.get_simulation(simulation_id)
        if not db_simulation:
            logger.warning(f"Simulation ID {simulation_id} not found for status update.")
            return None
        try:
            db_simulation.status = status
            if results_path is not None: # Allow explicitly setting results_path to None/empty
                db_simulation.results_path = results_path
            self.db.commit()
            self.db.refresh(db_simulation)
            logger.info(f"Simulation ID {simulation_id} status updated to '{status}'.")
            return db_simulation
        except SQLAlchemyError as e:
            logger.error(f"Error updating simulation ID {simulation_id}: {str(e)}")
            self.db.rollback()
            return None

    def get_simulations_for_reservoir(self, reservoir_id: int, skip: int = 0, limit: int = 100) -> List[Simulation]:
        """Get all simulations for a reservoir with pagination"""
        return self.db.query(Simulation).filter(Simulation.reservoir_id == reservoir_id).offset(skip).limit(limit).all()
