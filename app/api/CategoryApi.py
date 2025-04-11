from flask import Flask, Blueprint, flash, request, redirect, render_template, jsonify, url_for
from config.db import app, db, ma

from models.CategoryModel import Category, CategorySchema

ruta_category= Blueprint("route_category", __name__)

category_schema = CategorySchema()
category_schema = CategorySchema(many=True) 

@ruta_category.route("/categories" , methods=["GET"])
def getAllCategories():
    categories = Category.query.all() 
    result = category_schema.dump(categories)
    return jsonify(result)  

@ruta_category.route('/addCategory',methods=['POST'])
def addCategory():  
    namecategory = request.json['namecategory']
    newcategory = Category(namecategory)
    db.session.add(newcategory)
    db.session.commit()
    return "Guardado"

@ruta_category.route("/deleteCategory/<id>", methods=["DELETE"])
def deleteCategory(id):        
    categoryBd = Category.query.get(id)        
    db.session.delete(categoryBd)                     
    db.session.commit()    
    return "Eliminado con exito"

@ruta_category.route("/updateCategory", methods= ["PUT"])
def updateCategory(): 
    id = request.json['id']
    category = Category.query.get(id)       
    category.namecategory = request.json['namecategory']                           
    db.session.commit()                        
    return "Actualizado exitosamente"   

if __name__ == '__main__':
    app.run(debug=True)     


