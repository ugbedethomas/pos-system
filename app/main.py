from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app import crud, schemas
from app.database import get_db, SessionLocal

# Create FastAPI app
app = FastAPI(title="POS System", version="2.0.0")

# Mount templates
templates = Jinja2Templates(directory="templates")


# API endpoints (keep existing)
@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard")


# Web pages
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    # Get stats for dashboard
    products = crud.get_products(db)
    customers = crud.get_customers(db)
    sales = crud.get_sales(db)

    # Calculate today's sales
    today = date.today()
    today_sales = sum(sale.total_amount for sale in sales if sale.created_at.date() == today)

    # Calculate inventory value
    inventory_value = sum(p.stock_quantity * p.price for p in products)

    # Get low stock products
    low_stock_products = crud.get_low_stock_products(db)

    # Get recent sales (last 5)
    recent_sales = sorted(sales, key=lambda x: x.created_at, reverse=True)[:5]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_products": len(products),
        "total_customers": len(customers),
        "today_sales": today_sales,
        "inventory_value": inventory_value,
        "low_stock_products": low_stock_products,
        "low_stock_count": len(low_stock_products),
        "new_customers_today": 0,  # You can implement this
        "recent_sales": recent_sales
    })


@app.get("/pos", response_class=HTMLResponse)
def pos_page(request: Request, db: Session = Depends(get_db)):
    products = crud.get_products(db)
    categories = list(set(p.category for p in products if p.category))

    return templates.TemplateResponse("pos.html", {
        "request": request,
        "products": products,
        "categories": categories
    })


@app.get("/products", response_class=HTMLResponse)
def products_page(request: Request, db: Session = Depends(get_db)):
    products = crud.get_products(db)

    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": products
    })


@app.get("/inventory", response_class=HTMLResponse)
def inventory_page(request: Request, db: Session = Depends(get_db)):
    report = crud.get_inventory_report(db)
    low_stock = crud.get_low_stock_products(db)

    return templates.TemplateResponse("inventory.html", {
        "request": request,
        "inventory_report": report,
        "low_stock_products": low_stock
    })


@app.get("/sales", response_class=HTMLResponse)
def sales_page(request: Request, db: Session = Depends(get_db)):
    sales = crud.get_sales(db)

    return templates.TemplateResponse("sales.html", {
        "request": request,
        "sales": sales
    })


# API endpoints (for AJAX calls)
@app.get("/api/products/", response_model=List[schemas.Product])
def api_read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_products(db, skip=skip, limit=limit)


@app.post("/api/products/", response_model=schemas.Product)
def api_create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_product(db=db, product=product)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/products/{product_id}", response_model=schemas.Product)
def api_read_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id=product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/api/sales/", response_model=schemas.Sale)
def api_create_sale(sale: schemas.SaleCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_sale(db=db, sale=sale)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sales/", response_model=List[schemas.Sale])
def api_read_sales(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_sales(db, skip=skip, limit=limit)


@app.get("/api/inventory/report")
def api_inventory_report(db: Session = Depends(get_db)):
    return crud.get_inventory_report(db)


# Web form endpoints
@app.post("/products/create")
def web_create_product(
        request: Request,
        name: str = Form(...),
        price: float = Form(...),
        stock_quantity: int = Form(0),
        category: str = Form("Uncategorized"),
        sku: str = Form(...),
        db: Session = Depends(get_db)
):
    product = schemas.ProductCreate(
        name=name,
        price=price,
        stock_quantity=stock_quantity,
        category=category,
        sku=sku
    )

    try:
        crud.create_product(db, product)
        return RedirectResponse(url="/products", status_code=303)
    except ValueError as e:
        # In a real app, you'd show an error message
        return RedirectResponse(url="/products", status_code=303)


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)