# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import *
# from inventory.models import *


# @receiver(post_save, sender=InventoryAdjustment)
# def handle_inventory_adjustment(sender, instance, created, **kwargs):
#     if not created:
#         return

#     inventory, _ = Inventory.objects.get_or_create(
#         item=instance.item,
#         location=instance.location,
#         defaults={'quantity': 0}
#     )
#     inventory.quantity = instance.quantity_after or 0
#     inventory.save()


# @receiver(post_save, sender=InventoryReturn)
# def handle_inventory_return(sender, instance, created, **kwargs):
#     if not created:
#         return

#     if instance.location:
#         inventory, _ = Inventory.objects.get_or_create(
#             item=instance.item,
#             location=instance.location,
#             defaults={'quantity': 0}
#         )
#         inventory.quantity = max((inventory.quantity or 0) - (instance.quantity or 0), 0)
#         inventory.save()

# @receiver(post_save, sender=CycleCount)
# def handle_cycle_count(sender, instance, created, **kwargs):
#     if not created:
#         return

#     if instance.item and instance.location:
#         inventory, _ = Inventory.objects.get_or_create(
#             item=instance.item,
#             location=instance.location,
#             defaults={'quantity': 0}
#         )
#         inventory.quantity = instance.counted_quantity or 0
#         inventory.save()

# def log_inventory_change(item, location, action_code, quantity_changed, user, reference_id=None, reference_type=None):
#     try:
#         # Get the InventoryActionType record (e.g., code='transfer')
#         action_type = InventoryActionType.objects.get(code=action_code)

#         # Get the inventory record
#         inventory = Inventory.objects.get(item=item, location=location, deleted=False)

#         InventoryLog.objects.create(
#             inventory=inventory,
#             item=item,
#             location=location,
#             action_type=action_type,
#             reference_id=reference_id,
#             reference_type=reference_type,
#             quantity_before=inventory.quantity - quantity_changed,
#             quantity_changed=quantity_changed,
#             quantity_after=inventory.quantity,
#             changed_by=user,
#         )
#     except (Inventory.DoesNotExist, InventoryActionType.DoesNotExist):
#         pass

# @receiver(post_save, sender=InventoryTransfer)
# def handle_inventory_transfer(sender, instance, created, **kwargs):
#     if not created:
#         return

#     item = instance.item
#     qty = instance.quantity
#     user = instance.created_by
#     ref_id = instance.id

#     # FROM location (decrease stock)
#     from_inv, _ = Inventory.objects.get_or_create(item=item, location=instance.from_location, defaults={"quantity": 0})
#     from_inv.quantity = (from_inv.quantity or 0) - qty
#     from_inv.save()

#     log_inventory_change(
#         item=item,
#         location=instance.from_location,
#         action_code="transfer",
#         quantity_changed=-qty,
#         user=user,
#         reference_id=ref_id,
#         reference_type="InventoryTransfer"
#     )

#     # TO location (increase stock)
#     to_inv, _ = Inventory.objects.get_or_create(item=item, location=instance.to_location, defaults={"quantity": 0})
#     to_inv.quantity = (to_inv.quantity or 0) + qty
#     to_inv.save()

#     log_inventory_change(
#         item=item,
#         location=instance.to_location,
#         action_code="transfer",
#         quantity_changed=qty,
#         user=user,
#         reference_id=ref_id,
#         reference_type="InventoryTransfer"
#     )

# @receiver(post_save, sender=Inward)
# def update_supplier_rating(sender, instance, created, **kwargs):
#     if not created or not instance.purchase_order:
#         return

#     po = instance.purchase_order
#     supplier = po.supplier
#     expected_date = po.expected_delivery_date
#     actual_date = instance.date

#     # Delivery Delay in days
#     delay_days = (actual_date - expected_date).days if expected_date and actual_date else 0

#     # Current rating
#     previous_rating = supplier.supplier_rating or 5.0

#     # Simple logic:
#     if delay_days > 2:
#         new_rating = max(previous_rating - 0.2, 1.0)
#     elif delay_days > 0:
#         new_rating = max(previous_rating - 0.1, 1.0)
#     else:
#         new_rating = min(previous_rating + 0.1, 5.0)

#     # Optional: add quality check (if quality_status exists)
#     if hasattr(instance, "quality_status") and instance.quality_status and instance.quality_status.code == 'damaged':
#         new_rating = max(new_rating - 0.2, 1.0)

#     supplier.supplier_rating = round(new_rating, 2)
#     supplier.save()


from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import InventoryTransaction, InventoryProcessType, Inventory
from django.conf import settings


@receiver(post_save, sender=InventoryTransaction)
def handle_inventory_transaction(sender, instance, created, **kwargs):
    if not created:
        return

    item = instance.item
    qty = instance.quantity or 0
    user = instance.created_by
    process_code = instance.process_type.code
    ref_id = instance.id

    if process_code == 'INWARD':
        inv, _ = Inventory.objects.get_or_create(item=item, location=instance.location, defaults={'quantity': 0})
        quantity_before = inv.quantity or 0
        inv.quantity += qty
        inv.quantity_before = quantity_before
        inv.quantity_after = inv.quantity
        inv.updated_by = user
        inv.save()

    elif process_code == 'OUTWARD':
        inv, _ = Inventory.objects.get_or_create(item=item, location=instance.location, defaults={'quantity': 0})
        quantity_before = inv.quantity or 0
        inv.quantity -= qty
        inv.quantity_before = quantity_before
        inv.quantity_after = inv.quantity
        inv.updated_by = user
        inv.save()

    elif process_code == 'TRANSFER':
        # FROM location
        from_inv, _ = Inventory.objects.get_or_create(item=item, location=instance.from_location, defaults={"quantity": 0})
        quantity_before_from = from_inv.quantity or 0
        from_inv.quantity -= qty
        from_inv.quantity_before = quantity_before_from
        from_inv.quantity_after = from_inv.quantity
        from_inv.updated_by = user
        from_inv.save()

        # TO location
        to_inv, _ = Inventory.objects.get_or_create(item=item, location=instance.to_location, defaults={"quantity": 0})
        quantity_before_to = to_inv.quantity or 0
        to_inv.quantity += qty
        to_inv.quantity_before = quantity_before_to
        to_inv.quantity_after = to_inv.quantity
        to_inv.updated_by = user
        to_inv.save()

    elif process_code == 'RETURN':
        inv, _ = Inventory.objects.get_or_create(item=item, location=instance.location, defaults={"quantity": 0})
        quantity_before = inv.quantity or 0
        inv.quantity += qty
        inv.quantity_before = quantity_before
        inv.quantity_after = inv.quantity
        inv.updated_by = user
        inv.save()

    elif process_code == 'ADJUSTMENT':
        inv, _ = Inventory.objects.get_or_create(item=item, location=instance.location, defaults={"quantity": 0})
        quantity_before = inv.quantity or 0
        inv.quantity = qty
        inv.quantity_before = quantity_before
        inv.quantity_after = inv.quantity
        inv.updated_by = user
        inv.save()


@receiver(post_save, sender=InventoryTransaction)
def update_supplier_rating_on_inward(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.process_type.code != 'INWARD' or not instance.purchase_order:
        return

    po = instance.purchase_order
    supplier = po.supplier
    expected_date = po.expected_delivery_date
    actual_date = instance.date

    delay_days = (actual_date - expected_date).days if expected_date and actual_date else 0
    previous_rating = supplier.supplier_rating or 5.0

    if delay_days > 2:
        new_rating = max(previous_rating - 0.2, 1.0)
    elif delay_days > 0:
        new_rating = max(previous_rating - 0.1, 1.0)
    else:
        new_rating = min(previous_rating + 0.1, 5.0)

    supplier.supplier_rating = round(new_rating, 2)
    supplier.save()
