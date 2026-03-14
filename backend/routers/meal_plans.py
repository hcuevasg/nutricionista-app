"""Meal plan routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/meal-plans", tags=["meal_plans"])


@router.post("", response_model=schemas.MealPlanResponse)
async def create_meal_plan(
    patient_id: int,
    request: schemas.MealPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Create meal plan for patient."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Create plan
    meal_plan = models.MealPlan(
        patient_id=patient_id,
        name=request.name,
        date=request.date,
        goal=request.goal,
        calories=request.calories,
        protein_g=request.protein_g,
        carbs_g=request.carbs_g,
        fat_g=request.fat_g,
        notes=request.notes
    )
    db.add(meal_plan)
    db.flush()

    # Add items
    for item in request.items:
        meal_item = models.MealItem(
            plan_id=meal_plan.id,
            **item.model_dump()
        )
        db.add(meal_item)

    db.commit()
    db.refresh(meal_plan)
    return meal_plan


@router.get("/{patient_id}", response_model=List[schemas.MealPlanResponse])
async def list_meal_plans(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """List all meal plans for patient."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meal_plans = db.query(models.MealPlan).filter(
        models.MealPlan.patient_id == patient_id
    ).order_by(models.MealPlan.created_at.desc()).all()

    return meal_plans


@router.get("/{patient_id}/{plan_id}", response_model=schemas.MealPlanResponse)
async def get_meal_plan(
    patient_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Get specific meal plan."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meal_plan = db.query(models.MealPlan).filter(
        models.MealPlan.id == plan_id,
        models.MealPlan.patient_id == patient_id
    ).first()

    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    return meal_plan


@router.put("/{patient_id}/{plan_id}", response_model=schemas.MealPlanResponse)
async def update_meal_plan(
    patient_id: int,
    plan_id: int,
    request: schemas.MealPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Update meal plan."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meal_plan = db.query(models.MealPlan).filter(
        models.MealPlan.id == plan_id,
        models.MealPlan.patient_id == patient_id
    ).first()

    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    # Update fields
    meal_plan.name = request.name
    meal_plan.date = request.date
    meal_plan.goal = request.goal
    meal_plan.calories = request.calories
    meal_plan.protein_g = request.protein_g
    meal_plan.carbs_g = request.carbs_g
    meal_plan.fat_g = request.fat_g
    meal_plan.notes = request.notes

    # Delete old items
    db.query(models.MealItem).filter(models.MealItem.plan_id == plan_id).delete()

    # Add new items
    for item in request.items:
        meal_item = models.MealItem(
            plan_id=plan_id,
            **item.model_dump()
        )
        db.add(meal_item)

    db.commit()
    db.refresh(meal_plan)
    return meal_plan


@router.delete("/{patient_id}/{plan_id}")
async def delete_meal_plan(
    patient_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.Nutritionist = Depends(auth.get_current_user)
):
    """Delete meal plan."""
    # Verify patient belongs to user
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.nutritionist_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meal_plan = db.query(models.MealPlan).filter(
        models.MealPlan.id == plan_id,
        models.MealPlan.patient_id == patient_id
    ).first()

    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    db.delete(meal_plan)
    db.commit()

    return {"message": "Meal plan deleted"}
