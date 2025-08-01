from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from typing import Dict, Any, Optional, Tuple, List
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from .models import *
from tasks.models import *

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Enum for transaction types to avoid magic strings"""
    INWARD = "INWARD"
    OUTWARD = "OUTWARD"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN = "RETURN"


@dataclass
class TransactionResult:
    """Data class for transaction results"""
    success: bool
    transaction_id: int
    process_type: str
    message: str
    inventory_updated: bool = False
    tasks_created: List[int] = None
    quantity_before: float = 0
    quantity_after: float = 0
    quantity_changed: float = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.tasks_created is None:
            self.tasks_created = []
        if self.errors is None:
            self.errors = []


class TransactionProcessor(ABC):
    """Abstract base class for transaction processors"""
    
    def __init__(self, user):
        self.user = user
    
    @abstractmethod
    def process(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the transaction and return results"""
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """Validate transaction data and return list of errors"""
        pass


class InwardProcessor(TransactionProcessor):
    """Processor for inward transactions"""
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        errors = []
        if not data.get('item'):
            errors.append("Item is required for inward transaction")
        if not data.get('location'):
            errors.append("Location is required for inward transaction")
        if not data.get('quantity') or data['quantity'] <= 0:
            errors.append("Valid quantity is required for inward transaction")
        return errors
    
    def process(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Dict[str, Any]:
        item = transaction_obj.item
        location = transaction_obj.location
        quantity = transaction_obj.quantity
        
        # Get or create inventory record with caching
        cache_key = f"inventory_{item.id}_{location.id}_{data.get('batch', '')}_{data.get('lot', '')}"
        inventory = cache.get(cache_key)
        
        if not inventory:
            inventory, created = Inventory.objects.get_or_create(
                item=item,
                location=location,
                batch=data.get('batch'),
                lot=data.get('lot'),
                defaults={
                    'quantity': 0,
                    'reserved_quantity': 0,
                    'quality_status': data.get('quality_status'),
                    'expiry_date': data.get('expiry_date'),
                    'created_by': self.user,
                }
            )
            cache.set(cache_key, inventory, 300)  # Cache for 5 minutes
        
        # Update inventory
        old_quantity = inventory.quantity or 0
        inventory.quantity = old_quantity + quantity
        inventory.updated_by = self.user
        inventory.last_action = 'INWARD'
        inventory.last_changed_quantity = quantity
        inventory.last_reference_id = transaction_obj.id
        inventory.last_reference_type = 'InventoryTransaction'
        inventory.save()
        
        # Invalidate cache
        cache.delete(cache_key)
        
        return {
            "inventory_updated": True,
            "quantity_before": old_quantity,
            "quantity_after": inventory.quantity,
            "quantity_added": quantity,
        }


class OutwardProcessor(TransactionProcessor):
    """Processor for outward transactions"""
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        errors = []
        if not data.get('item'):
            errors.append("Item is required for outward transaction")
        if not data.get('location'):
            errors.append("Location is required for outward transaction")
        if not data.get('quantity') or data['quantity'] <= 0:
            errors.append("Valid quantity is required for outward transaction")
        
        # Check stock availability
        if data.get('item') and data.get('location'):
            available = self._check_stock_availability(
                data['item'], data['location'], data['quantity'],
                data.get('batch'), data.get('lot')
            )
            if not available:
                errors.append("Insufficient stock available")
        
        return errors
    
    def _check_stock_availability(self, item, location, quantity, batch=None, lot=None) -> bool:
        try:
            inventory = Inventory.objects.get(
                item=item,
                location=location,
                batch=batch,
                lot=lot,
                deleted=False
            )
            available_quantity = (inventory.quantity or 0) - (inventory.reserved_quantity or 0)
            return available_quantity >= quantity
        except Inventory.DoesNotExist:
            return False
    
    def process(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Dict[str, Any]:
        item = transaction_obj.item
        location = transaction_obj.location
        quantity = transaction_obj.quantity
        
        # Get inventory record
        try:
            inventory = Inventory.objects.get(
                item=item,
                location=location,
                batch=data.get('batch'),
                lot=data.get('lot'),
                deleted=False
            )
        except Inventory.DoesNotExist:
            raise ValidationError(f"No inventory found for item {item.name} at location {location.code}")
        
        # Check stock availability again (double-check)
        available_quantity = (inventory.quantity or 0) - (inventory.reserved_quantity or 0)
        if available_quantity < quantity:
            raise ValidationError(
                f"Insufficient stock. Available: {available_quantity}, Requested: {quantity}"
            )
        
        # Update inventory
        old_quantity = inventory.quantity or 0
        inventory.quantity = old_quantity - quantity
        inventory.updated_by = self.user
        inventory.last_action = 'OUTWARD'
        inventory.last_changed_quantity = -quantity
        inventory.last_reference_id = transaction_obj.id
        inventory.last_reference_type = 'InventoryTransaction'
        inventory.save()
        
        return {
            "inventory_updated": True,
            "quantity_before": old_quantity,
            "quantity_after": inventory.quantity,
            "quantity_deducted": quantity,
        }


class TransferProcessor(TransactionProcessor):
    """Processor for transfer transactions"""
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        errors = []
        if not data.get('item'):
            errors.append("Item is required for transfer transaction")
        if not data.get('from_location'):
            errors.append("From location is required for transfer transaction")
        if not data.get('to_location'):
            errors.append("To location is required for transfer transaction")
        if not data.get('quantity') or data['quantity'] <= 0:
            errors.append("Valid quantity is required for transfer transaction")
        
        if data.get('from_location') == data.get('to_location'):
            errors.append("From and to locations cannot be the same")
        
        # Check source stock availability
        if data.get('item') and data.get('from_location') and data.get('quantity'):
            available = self._check_source_stock_availability(
                data['item'], data['from_location'], data['quantity'],
                data.get('batch'), data.get('lot')
            )
            if not available:
                errors.append("Insufficient stock at source location")
        
        return errors
    
    def _check_source_stock_availability(self, item, from_location, quantity, batch=None, lot=None) -> bool:
        try:
            inventory = Inventory.objects.get(
                item=item,
                location=from_location,
                batch=batch,
                lot=lot,
                deleted=False
            )
            return (inventory.quantity or 0) >= quantity
        except Inventory.DoesNotExist:
            return False
    
    def process(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Dict[str, Any]:
        item = transaction_obj.item
        from_location = transaction_obj.from_location
        to_location = transaction_obj.to_location
        quantity = transaction_obj.quantity
        
        # Get source inventory
        try:
            source_inventory = Inventory.objects.get(
                item=item,
                location=from_location,
                batch=data.get('batch'),
                lot=data.get('lot'),
                deleted=False
            )
        except Inventory.DoesNotExist:
            raise ValidationError(f"No inventory found at source location {from_location.code}")
        
        # Check source stock availability
        source_quantity = source_inventory.quantity or 0
        if source_quantity < quantity:
            raise ValidationError(
                f"Insufficient stock at source. Available: {source_quantity}, Requested: {quantity}"
            )
        
        # Get or create destination inventory
        dest_inventory, created = Inventory.objects.get_or_create(
            item=item,
            location=to_location,
            batch=data.get('batch'),
            lot=data.get('lot'),
            defaults={
                'quantity': 0,
                'reserved_quantity': 0,
                'quality_status': source_inventory.quality_status,
                'expiry_date': source_inventory.expiry_date,
                'created_by': self.user,
            }
        )
        
        # Update both inventories atomically
        source_inventory.quantity = source_quantity - quantity
        source_inventory.updated_by = self.user
        source_inventory.last_action = 'TRANSFER_OUT'
        source_inventory.last_changed_quantity = -quantity
        source_inventory.last_reference_id = transaction_obj.id
        source_inventory.last_reference_type = 'InventoryTransaction'
        source_inventory.save()
        
        dest_old_quantity = dest_inventory.quantity or 0
        dest_inventory.quantity = dest_old_quantity + quantity
        dest_inventory.updated_by = self.user
        dest_inventory.last_action = 'TRANSFER_IN'
        dest_inventory.last_changed_quantity = quantity
        dest_inventory.last_reference_id = transaction_obj.id
        dest_inventory.last_reference_type = 'InventoryTransaction'
        dest_inventory.save()
        
        return {
            "inventory_updated": True,
            "source_quantity_before": source_quantity,
            "source_quantity_after": source_inventory.quantity,
            "dest_quantity_before": dest_old_quantity,
            "dest_quantity_after": dest_inventory.quantity,
            "quantity_transferred": quantity,
        }


class AdjustmentProcessor(TransactionProcessor):
    """Processor for adjustment transactions"""
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        errors = []
        if not data.get('item'):
            errors.append("Item is required for adjustment transaction")
        if not data.get('location'):
            errors.append("Location is required for adjustment transaction")
        if not data.get('quantity'):
            errors.append("Quantity is required for adjustment transaction")
        
        return errors
    
    def process(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Dict[str, Any]:
        item = transaction_obj.item
        location = transaction_obj.location
        adjustment_quantity = transaction_obj.quantity
        
        # Get inventory record
        try:
            inventory = Inventory.objects.get(
                item=item,
                location=location,
                batch=data.get('batch'),
                lot=data.get('lot'),
                deleted=False
            )
        except Inventory.DoesNotExist:
            raise ValidationError(f"No inventory found for item {item.name} at location {location.code}")
        
        # Update inventory
        old_quantity = inventory.quantity or 0
        new_quantity = old_quantity + adjustment_quantity
        
        # Prevent negative stock unless explicitly allowed
        if new_quantity < 0 and not data.get('allow_negative', False):
            raise ValidationError(f"Adjustment would result in negative stock: {new_quantity}")
        
        inventory.quantity = new_quantity
        inventory.updated_by = self.user
        inventory.last_action = 'ADJUSTMENT'
        inventory.last_changed_quantity = adjustment_quantity
        inventory.last_reference_id = transaction_obj.id
        inventory.last_reference_type = 'InventoryTransaction'
        inventory.save()
        
        return {
            "inventory_updated": True,
            "quantity_before": old_quantity,
            "quantity_after": new_quantity,
            "adjustment_amount": adjustment_quantity,
        }


class ReturnProcessor(TransactionProcessor):
    """Processor for return transactions"""
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        errors = []
        if not data.get('item'):
            errors.append("Item is required for return transaction")
        if not data.get('location'):
            errors.append("Location is required for return transaction")
        if not data.get('quantity') or data['quantity'] <= 0:
            errors.append("Valid quantity is required for return transaction")
        
        return errors
    
    def process(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Dict[str, Any]:
        item = transaction_obj.item
        location = transaction_obj.location
        return_quantity = transaction_obj.quantity
        is_defective = transaction_obj.is_defective
        
        # Get inventory record
        try:
            inventory = Inventory.objects.get(
                item=item,
                location=location,
                batch=data.get('batch'),
                lot=data.get('lot'),
                deleted=False
            )
        except Inventory.DoesNotExist:
            raise ValidationError(f"No inventory found for item {item.name} at location {location.code}")
        
        old_quantity = inventory.quantity or 0
        
        # Only update stock if not defective
        if not is_defective:
            inventory.quantity = old_quantity + return_quantity
            inventory.updated_by = self.user
            inventory.last_action = 'RETURN'
            inventory.last_changed_quantity = return_quantity
            inventory.last_reference_id = transaction_obj.id
            inventory.last_reference_type = 'InventoryTransaction'
            inventory.save()
            new_quantity = inventory.quantity
        else:
            new_quantity = old_quantity
        
        return {
            "inventory_updated": not is_defective,
            "quantity_before": old_quantity,
            "quantity_after": new_quantity,
            "quantity_returned": return_quantity if not is_defective else 0,
            "is_defective": is_defective,
        }


class TaskManager:
    """Manages task creation for transactions"""
    
    def __init__(self, user):
        self.user = user
        self.task_types = self._get_task_types()
    
    def _get_task_types(self) -> Dict[str, TaskType]:
        """Cache task types for better performance"""
        return {
            tt.code: tt for tt in TaskType.objects.filter(is_active=True)
        }
    
    def create_related_tasks(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create related tasks based on transaction type"""
        process_type = transaction_obj.process_type.code
        tasks_created = []
        
        try:
            if process_type == TransactionType.INWARD.value:
                task = self._create_putaway_task(transaction_obj, data)
                if task:
                    tasks_created.append(task)
                    
            elif process_type == TransactionType.OUTWARD.value:
                task = self._create_pickup_task(transaction_obj, data)
                if task:
                    tasks_created.append(task)
                    
            elif process_type == TransactionType.TRANSFER.value:
                task = self._create_transfer_task(transaction_obj, data)
                if task:
                    tasks_created.append(task)
        
        except Exception as e:
            logger.warning(f"Failed to create related tasks: {e}")
            # Don't fail the transaction if task creation fails
        
        return {
            "tasks_created": [task.id for task in tasks_created],
            "task_count": len(tasks_created)
        }
    
    def _create_putaway_task(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Optional[InventoryTask]:
        """Create putaway task for inward transaction"""
        task_type = self.task_types.get('PUTAWAY')
        if not task_type:
            logger.warning("PUTAWAY task type not configured")
            return None
        
        return InventoryTask.objects.create(
            task_type=task_type,
            transaction=transaction_obj,
            item=transaction_obj.item,
            to_location=transaction_obj.location,
            quantity=transaction_obj.quantity,
            assigned_to=data.get('assigned_to'),
            created_by=self.user,
        )
    
    def _create_pickup_task(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Optional[InventoryTask]:
        """Create pickup task for outward transaction"""
        task_type = self.task_types.get('PICKUP')
        if not task_type:
            logger.warning("PICKUP task type not configured")
            return None
        
        return InventoryTask.objects.create(
            task_type=task_type,
            transaction=transaction_obj,
            item=transaction_obj.item,
            from_location=transaction_obj.location,
            quantity=transaction_obj.quantity,
            assigned_to=data.get('assigned_to'),
            created_by=self.user,
        )
    
    def _create_transfer_task(self, transaction_obj: InventoryTransaction, data: Dict[str, Any]) -> Optional[InventoryTask]:
        """Create transfer task for transfer transaction"""
        task_type = self.task_types.get('TRANSFER')
        if not task_type:
            logger.warning("TRANSFER task type not configured")
            return None
        
        return InventoryTask.objects.create(
            task_type=task_type,
            transaction=transaction_obj,
            item=transaction_obj.item,
            from_location=transaction_obj.from_location,
            to_location=transaction_obj.to_location,
            quantity=transaction_obj.quantity,
            assigned_to=data.get('assigned_to'),
            created_by=self.user,
        )


class InventoryTransactionService:
    """Centralized service for handling all inventory transactions with improved scalability"""
    
    def __init__(self, user):
        self.user = user
        self.process_types = self._get_process_types()
        self.task_manager = TaskManager(user)
        self.processors = self._get_processors()
    
    def _get_process_types(self) -> Dict[str, InventoryProcessType]:
        """Cache process types for better performance"""
        cache_key = "inventory_process_types"
        process_types = cache.get(cache_key)
        
        if not process_types:
            process_types = {
                pt.code: pt for pt in InventoryProcessType.objects.filter(is_active=True)
            }
            cache.set(cache_key, process_types, 3600)  # Cache for 1 hour
        
        return process_types
    
    def _get_processors(self) -> Dict[str, TransactionProcessor]:
        """Get processor instances"""
        return {
            TransactionType.INWARD.value: InwardProcessor(self.user),
            TransactionType.OUTWARD.value: OutwardProcessor(self.user),
            TransactionType.TRANSFER.value: TransferProcessor(self.user),
            TransactionType.ADJUSTMENT.value: AdjustmentProcessor(self.user),
            TransactionType.RETURN.value: ReturnProcessor(self.user),
        }
    
    def create_transaction(self, data: Dict[str, Any]) -> TransactionResult:
        """
        Centralized method to create any type of inventory transaction
        Returns: TransactionResult object
        """
        try:
            # Validate process type
            process_type_code = data.get('process_type')
            if not process_type_code:
                return TransactionResult(
                    success=False,
                    transaction_id=0,
                    process_type="",
                    message="Process type is required",
                    errors=["Process type is required"]
                )
            
            if process_type_code not in self.process_types:
                return TransactionResult(
                    success=False,
                    transaction_id=0,
                    process_type=process_type_code,
                    message=f"Invalid process type: {process_type_code}",
                    errors=[f"Invalid process type: {process_type_code}"]
                )
            
            # Get processor and validate
            processor = self.processors.get(process_type_code)
            if not processor:
                return TransactionResult(
                    success=False,
                    transaction_id=0,
                    process_type=process_type_code,
                    message=f"No processor found for process type: {process_type_code}",
                    errors=[f"No processor found for process type: {process_type_code}"]
                )
            
            # Validate transaction data
            validation_errors = processor.validate(data)
            if validation_errors:
                return TransactionResult(
                    success=False,
                    transaction_id=0,
                    process_type=process_type_code,
                    message="Validation failed",
                    errors=validation_errors
                )
            
            # Process transaction
            with transaction.atomic():
                # Create transaction record
                transaction_obj = self._create_transaction_record(data)
                
                # Process based on transaction type
                process_result = processor.process(transaction_obj, data)
                
                # Create related tasks if needed
                task_result = self.task_manager.create_related_tasks(transaction_obj, data)
                
                return TransactionResult(
                    success=True,
                    transaction_id=transaction_obj.id,
                    process_type=transaction_obj.process_type.code,
                    message=f"{transaction_obj.process_type.name} transaction created successfully",
                    inventory_updated=process_result.get("inventory_updated", False),
                    tasks_created=task_result.get("tasks_created", []),
                    quantity_before=process_result.get("quantity_before", 0),
                    quantity_after=process_result.get("quantity_after", 0),
                    quantity_changed=process_result.get("quantity_added", 0) or 
                                  process_result.get("quantity_deducted", 0) or
                                  process_result.get("quantity_transferred", 0) or
                                  process_result.get("adjustment_amount", 0) or
                                  process_result.get("quantity_returned", 0)
                )
                
        except ValidationError as e:
            logger.error(f"Validation error in transaction creation: {e}")
            return TransactionResult(
                success=False,
                transaction_id=0,
                process_type=data.get('process_type', ''),
                message=str(e),
                errors=[str(e)]
            )
        except Exception as e:
            logger.error(f"Error creating inventory transaction: {e}")
            return TransactionResult(
                success=False,
                transaction_id=0,
                process_type=data.get('process_type', ''),
                message="Internal server error",
                errors=[str(e)]
            )
    
    def _create_transaction_record(self, data: Dict[str, Any]) -> InventoryTransaction:
        """Create the base transaction record"""
        process_type_code = data['process_type']
        
        # Set required fields
        transaction_data = {
            'process_type': self.process_types[process_type_code],
            'item': data['item'],
            'quantity': data['quantity'],
            'created_by': self.user,
            'remarks': data.get('remarks', ''),
            'reference_number': data.get('reference_number', ''),
        }
        
        # Set location fields based on transaction type
        if process_type_code == TransactionType.TRANSFER.value:
            transaction_data.update({
                'from_location': data.get('from_location'),
                'to_location': data.get('to_location'),
            })
        else:
            transaction_data['location'] = data.get('location')
        
        # Set additional fields for specific transaction types
        if process_type_code == TransactionType.INWARD.value:
            transaction_data.update({
                'supplier': data.get('supplier'),
                'purchase_order': data.get('purchase_order'),
                'delivery_note': data.get('delivery_note'),
                'invoice_number': data.get('invoice_number'),
                'payment_terms': data.get('payment_terms'),
                'supplier_rating': data.get('supplier_rating'),
            })
        elif process_type_code == TransactionType.OUTWARD.value:
            transaction_data.update({
                'is_dispatched': data.get('is_dispatched', False),
                'dispatched_by': self.user if data.get('is_dispatched') else None,
                'dispatched_at': timezone.now() if data.get('is_dispatched') else None,
            })
        elif process_type_code == TransactionType.RETURN.value:
            transaction_data['is_defective'] = data.get('is_defective', False)
        
        return InventoryTransaction.objects.create(**transaction_data)


class InventoryValidationService:
    """Service for validating inventory operations with caching"""
    
    @staticmethod
    def validate_stock_availability(item: Item, location: Location, quantity: float, 
                                 batch=None, lot=None) -> bool:
        """Validate if sufficient stock is available with caching"""
        cache_key = f"stock_availability_{item.id}_{location.id}_{batch}_{lot}"
        result = cache.get(cache_key)
        
        if result is None:
            try:
                inventory = Inventory.objects.get(
                    item=item,
                    location=location,
                    batch=batch,
                    lot=lot,
                    deleted=False
                )
                available_quantity = (inventory.quantity or 0) - (inventory.reserved_quantity or 0)
                result = available_quantity >= quantity
                cache.set(cache_key, result, 60)  # Cache for 1 minute
            except Inventory.DoesNotExist:
                result = False
                cache.set(cache_key, result, 60)
        
        return result
    
    @staticmethod
    def validate_item_exists(item_id: int) -> bool:
        """Validate if item exists and is active with caching"""
        cache_key = f"item_exists_{item_id}"
        result = cache.get(cache_key)
        
        if result is None:
            try:
                item = Item.objects.get(id=item_id, deleted=False, is_active=True)
                result = True
                cache.set(cache_key, result, 300)  # Cache for 5 minutes
            except Item.DoesNotExist:
                result = False
                cache.set(cache_key, result, 300)
        
        return result
    
    @staticmethod
    def validate_location_exists(location_id: int) -> bool:
        """Validate if location exists and is active with caching"""
        cache_key = f"location_exists_{location_id}"
        result = cache.get(cache_key)
        
        if result is None:
            try:
                location = Location.objects.get(id=location_id, deleted=False, is_active=True)
                result = True
                cache.set(cache_key, result, 300)  # Cache for 5 minutes
            except Location.DoesNotExist:
                result = False
                cache.set(cache_key, result, 300)
        
        return result 