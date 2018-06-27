from flask import Blueprint, Flask, request, json, jsonify, make_response, url_for, abort
import jwt
import datetime
from datetime import datetime
from ..user.user_views import token_required, logged_in_user
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import swag_from
from ..app_models import Business, db, User
from flask_paginate import Pagination, get_page_args, get_page_parameter
from flask_cors import CORS, cross_origin
from ..user.user_views import SECRET_KEY


businessBlueprint = Blueprint('business', __name__)

CORS(businessBlueprint)

@businessBlueprint.route('/api/businesses', methods=['POST'])
# @cross_origin()
@swag_from('apidocs/create_business.yml')
@token_required
def create_business():
    # global logged_in_user
    token = request.headers.get('x-access-token')
    payload = jwt.decode(token, SECRET_KEY)
    # print(payload['id'])
    jsn = request.data
    data = json.loads(jsn)
    specialChars = ['@', '#', '$', '%', '^', '&', '*', '!', '/', '?', '-', '_']

    if len(data.keys()) == 0:
        return jsonify({'message':'fill in all the fields that is name, location, category and description'}), 400 #bad request

    # if len(data.keys()) != 4:
    #     return jsonify({'message':'cannot create business because of missing fields'}), 400 #bad request
    
    if 'name' not in data.keys():
        return jsonify({'message':'business name is missing'}), 400 #bad request

    if 'location' not in data.keys():
        return jsonify({'message':'business location is missing'}), 400 #bad request

    if 'category' not in data.keys():
        return jsonify({'message':'business category is missing'}), 400 #bad request

    if 'description' not in data.keys():
        return jsonify({'message':'business description is missing'}), 400 #bad request

    if len(data['name']) < 5:
        return jsonify({'message':'name of business is too short, should between five and ten characters'}), 400 #bad request

    if len(data['name']) > 50:
        return jsonify({'message':'name of business is too long, should between five and ten characters'}), 400 #bad request

    # if not logged_in_user:
    #     return jsonify({'message':'you are not logged in, please login'}), 401 # unauthorised access

    # payload = jwt.decode(token, SECRET_KEY)
    
    #lets pick the data from json passed
    business_name = data['name']
    user_id = int(payload['id'])
    location =data['location']
    category = data['category']
    description = data['description']

    for x in business_name:
        if x in specialChars:
            return jsonify({'message':'business name contains special characters'}), 400

    
    if Business.query.filter_by(business_name=business_name).count() == 0:
        business = Business(user_id, business_name, location, category, description)
        db.session.add(business)
        
        if business:
            return jsonify({'message':'business has been successfully created'}), 201
        else:
            return jsonify({'message':'business was not created, please try again'}), 400
    else:
        return jsonify({'message':'business already exists, please try again'}), 400

@businessBlueprint.route('/api/businesses/<int:id>', methods=['GET'])
@swag_from('retrieve_business.yml')
@token_required
def get_one_business(id):
    biz = Business.query.get(id)
    if biz:
        return jsonify({'businesses':biz.returnJson()}), 200
    else:
        return jsonify({'message':'no business with that id exists'}), 404

# route should look like 127.0.0.1:5000/api/businesses?page=<number>&limit=<number> 
@businessBlueprint.route('/api/businesses', methods=['GET']) 
@swag_from('retrieve_all_businesses.yml')
@token_required
def get_all_businesses():
    if request.method == 'GET':
        try:
            limit = request.args.get('limit') or 10 # default is 5 in case limit is not set
            page = request.args.get('page') or 1
            limit = int(limit)
            page = int(page)
            businesses = Business.query.paginate(per_page=limit, page=page, error_out=False)
            business_list =[]
            for business in businesses.items:
                business_obj = {
                    'id':business.id,
                    'name':business.business_name,
                    'user_id':business.user_id,
                    'location':business.location,
                    'category':business.category,
                    'description':business.description,
                    'date_created':business.date_created,
                    'date_modified':business.date_modified,
                    'per_page':businesses.per_page,
                    'current_page':businesses.page,
                    'total':businesses.total
                }
                business_list.append(business_obj)
            
            return jsonify({'businesses':[business for business in business_list]}), 200
        except Exception:
            return jsonify({"message":'limit and page should be integer values'}), 400


@businessBlueprint.route('/api/businesses/<int:business_id>', methods=['PUT'])
@swag_from('update_business.yml')
@token_required
def update_business(business_id):
    global logged_in_user
    jsn = request.data
    data = json.loads(jsn)
    biz = Business.query.get(int(business_id))

    if not logged_in_user:
        return jsonify({"message":"please login"}), 401

    if len(data.keys()) == 0:
        return jsonify({'message':'no information was provided for update'}), 400

    if not biz:
        return jsonify({'message':'no business with that id exists'}), 400

    user_id = logged_in_user['id']
    
    if biz.query.count() > 0 and user_id == biz.user_id:
        specialChars = ['@', '#', '$', '%', '^', '&', '*', '!', '/', '?', '-', '_']
        if 'name' in data.keys():
            business_name = data['name']

            if len(business_name) < 5:
                return jsonify({'message':'name of business is too short, should between five and fifty characters'}), 400 #bad request

            if len(business_name) > 50:
                return jsonify({'message':'name of business is too long, should between five and fifty characters'}), 400 #bad request

            for x in business_name:
                if x in specialChars:
                    return jsonify({'message':'business name contains special characters'}), 400
        else:
            business_name = ''

        if 'location' in data.keys():
            location =data['location']
        else:
            location = ''

        if 'category' in data.keys():
            category = data['category']
        else:
            category = ''

        if 'description' in data.keys():
            description = data['description']
        else:
            description = ''        
            
        if business_name:
            biz.business_name = business_name
        if location:
            biz.location = location
        if category:
            biz.category = category
        if description:
            biz.description = description   

        biz.date_modified = datetime.now()
        db.session.add(biz)
        db.session.commit()
        return jsonify({'message':'business has been updated successfully'}), 200
    else:
        return jsonify({'message':'no business with that id exists'}), 404

        
@businessBlueprint.route('/api/businesses/<int:business_id>', methods=['DELETE'])
@swag_from('delete_business.yml')
@token_required
def delete_business(business_id):
    global logged_in_user    
    biz = Business.query.get(int(business_id))

    if not logged_in_user:
        return jsonify({"message": "please login"}), 400

    user_id = logged_in_user['id']    
    if biz:
        if str(user_id) == str(biz.id):
            db.session.delete(biz)
            db.session.commit()
            return jsonify({'message':'business was deleted successfully'}), 200
        else:
            return jsonify({'message':'business was not deleted because you are not the owner'}), 400
    else:
        return jsonify({'message':'no business with that id exists'}), 400


@businessBlueprint.route('/api/businesses/search', methods=['GET'])
@swag_from('search_business.yml')
@token_required
def search_business():
    name = request.args.get('q')
    filter_type = str(request.args.get('filter_type'))
    filter_value = str(request.args.get('filter_value'))

    if name == '':
        return jsonify({'message':'no name to search for'}), 400

    if request.method == 'GET':
        limit = request.args.get('limit') or 2 # default is 5 in case limit is not set
        page = request.args.get('page') or 1
        limit = int(limit)
        page = int(page)

    if filter_value == '':
        return jsonify({'message':'filter value missing'}), 404

    if filter_type == 'location':
        results = Business.query.filter_by(location=filter_value).filter(Business.business_name.ilike("%"+ name +"%"))
        businesses = results.paginate(per_page=limit, page=page, error_out=False)
        business_list =[]
        for business in businesses.items:
            business_obj = {
                'id':business.id,
                'name':business.business_name,
                'user_id':business.user_id,
                'location':business.location,
                'category':business.category,
                'description':business.description,
                'date_created':business.date_created,
                'date_modified':business.date_modified,
                'per_page':businesses.per_page,
                'current_page':businesses.page,
                'total':businesses.total
            }
            business_list.append(business_obj)

    
    elif filter_type == 'category':
        results = Business.query.filter_by(category=filter_value).filter(Business.business_name.ilike("%"+ name +"%"))
        businesses = results.paginate(per_page=limit, page=page, error_out=False)
        business_list =[]
        for business in businesses.items:
            business_obj = {
                'id':business.id,
                'name':business.business_name,
                'user_id':business.user_id,
                'location':business.location,
                'category':business.category,
                'description':business.description,
                'date_created':business.date_created,
                'date_modified':business.date_modified,
                'per_page':businesses.per_page,
                'current_page':businesses.page,
                'total':businesses.total
            }
            business_list.append(business_obj)
    else:
        return jsonify({'message':'invalid or unknown filter type passed in query url'}), 400

    if len(business_list) > 0:
        return jsonify({'businesses':business_list}), 200
    else:
        return jsonify({'message':'no businesses match your search'}), 404


@businessBlueprint.route('/api/businesses/filter', methods=['GET'])
@swag_from('filter_business.yml')
@token_required
def filter_business():
    filter = str(request.args.get('filter'))
    filter_value = str(request.args.get('filter_value'))

    if request.method == 'GET':
        limit = request.args.get('limit') or 2 # default is 2 in case limit is not set
        page = request.args.get('page') or 1
        limit = int(limit)
        page = int(page)

    if filter == 'location':
        results = Business.query.filter_by(location=filter_value)
        businesses = results.paginate(per_page=limit, page=page, error_out=False)
        business_list =[]
        for business in businesses.items:
            business_obj = {
                'id':business.id,
                'name':business.business_name,
                'user_id':business.user_id,
                'location':business.location,
                'category':business.category,
                'description':business.description,
                'date_created':business.date_created,
                'date_modified':business.date_modified,
                'per_page':businesses.per_page,
                'current_page':businesses.page,
                'total':businesses.total
            }
            business_list.append(business_obj)

    elif filter == 'category':
        results = Business.query.filter_by(category=filter_value)
        businesses = results.paginate(per_page=limit, page=page, error_out=False)
        business_list =[]
        for business in businesses.items:
            business_obj = {
                'id':business.id,
                'name':business.business_name,
                'user_id':business.user_id,
                'location':business.location,
                'category':business.category,
                'description':business.description,
                'date_created':business.date_created,
                'date_modified':business.date_modified,
                'per_page':businesses.per_page,
                'current_page':businesses.page,
                'total':businesses.total
            }
            business_list.append(business_obj)
    else:
        return jsonify({'message':'invalid or unknown filter type passed in query url'}), 400
    print(business_list)
    if len(business_list) > 0:
        return jsonify({"message":business_list}), 200
    else:
        return jsonify({"message":'no businesses found'}), 404
