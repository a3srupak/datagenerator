import json
import logging 
import time
import threading
logger = logging.getLogger()
logger.setLevel(logging.INFO)
import secrets
from random import randrange
from datetime import datetime, timedelta, timezone
import random
import os
from decimal import Decimal
from faker import Faker
import boto3
dynamodb = boto3.resource('dynamodb')
from boto3.dynamodb.conditions import Key, Attr
fake = Faker()

SUBDIVISION=1000
NO_OF_LOOP = []

def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)


d1 = datetime.strptime("01/01/2000 00:00:00", "%d/%m/%Y %H:%M:%S")
d2 = datetime.strptime("31/12/2030 23:59:59", "%d/%m/%Y %H:%M:%S")

# current_date = random_date(d1, d2).isoformat()
# future_date = random_date(d1, d2).isoformat()
# current_iso_time = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().split('+')[0]

# while current_iso_time < current_date: current_date = random_date(d1, d2).isoformat()   # Old date

# while current_iso_time > future_date: future_date = random_date(d1, d2).isoformat()   # Future date


def insert_bulkdata(table_data):
    table = dynamodb.Table(os.environ["DATA_TABLE"])
    try:
        with table.batch_writer() as writer:
            for item in table_data:
                writer.put_item(Item=item)
        logger.info("Loaded data into table %s.", table.name)
    except Exception as e:
        logger.exception("Couldn't load data into table %s.", table.name)
        raise
# Role Id function
def role_ID_fuc(role_name):
    options = {'Bidding Representative':111, 'Sponsor':222, 'Market Monitor':333, 'Jurisdiction Administrator':444 }
    if role_name in options:
        roleId = options.get(role_name)
        return roleId

# Role type function       
def role_type_fun(role_type):
    options = {'Jurisdiction Member':777, 'Bidding Representative':888, 'System Administrator':999 }
    if role_type in options:
        role_type_Id = options.get(role_type)
        return role_type_Id

def data_generator(users_count,jurisdictionID,delay):
    data = []
    NO_OF_LOOP.append(users_count)
    time.sleep(delay)
    for i in range(users_count):
        current_date = random_date(d1, d2).isoformat()
        future_date = random_date(d1, d2).isoformat()
        current_iso_time = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().split('+')[0]
        while current_iso_time < current_date: current_date = random_date(d1, d2).isoformat()   # Old date
        while current_iso_time > future_date: future_date = random_date(d1, d2).isoformat()     # Future date
        
        role_name= random.choice(['Bidding Representative', 'Sponsor', 'Market Monitor', 'Jurisdiction Administrator']) # Role Name
        role_type= random.choice(['Jurisdiction Member', 'Bidding Representative', 'System Administrator'])   # Role type
        res_items = {
                "jurisdictionID" : jurisdictionID,
                "internal_userid" : secrets.token_hex(16),
                "jurisdiction_status": random.choice(['new','active','paused','linked','ended']),
                "registration_requested_datetime" : current_date, 
                "registration_approved_datetime" : future_date,
                "first_name" : fake.first_name(),
                "last_name" :fake.last_name(),
                "user_ID" : fake.user_name().lower(),
                "created_datetime" : current_date,
                "created_user_id" : random.choice(['john','martene','bill','joseph','jack']),
                "email_address" : fake.email(),
                "phone_number" : {
                                  "number1":fake.phone_number().replace('x','1'),
                                  "number2":fake.phone_number().replace('x','1'),
                                  "number3":fake.phone_number().replace('x','1')
                                  },
                "entity_name" : fake.company(),
                "entity_ID": fake.ripe_id(),
                "registration_status" : random.choice(['none','pending','declined','ended']),
                "addresses" : {
                                "address_type": random.choice(['home','office','shipping']),
                                "street_1": fake.street_address(),
                                "street_2": fake.building_number(),
                                "city": fake.city(),
                                "state_province": fake.state(),
                                "postal_zip_code": fake.postcode(),
                                "country": fake.country()
                            },
                "status" : random.choice(['pending','registered','rejected','ended']),
                "pause_status" : random.choice(['active','paused']),
                "roles" : {
                            "role_name": role_name,
                            "roleID": role_ID_fuc(role_name),
                            "role_type": role_type,
                            "role_type_ID":role_type_fun(role_type)
                        },
                "last_active" : current_date,
                "is_active_now" : random.choice(['Yes','No']),
                "last_event_name" : random.choice(['Auction','Sale','Meetup','Concert'])+' '+fake.month_name()+' '+fake.day_of_month()+' '+fake.year(),
                "last_event_ID" : fake.aba(),
                "account_balance" : random. randint(0.00,20000000),
                "currency_type" : random.choice(['USD','CAD']),
                "allowance_inventory":random. randint(1,1000000)
            }
        #print(res_items)
        data.append(res_items)
        #logger.info(res_items)
    insert_bulkdata(data)


def lambda_handler(event, context):
    http_method = event.get('httpMethod')
    logger.info(event)
    NO_OF_LOOP=[]
    if http_method == 'POST':
        body = event.get('body')
        users_count = ''
        jurisdictionID = ''
        if body is not None:
            users_count = int(json.loads(body).get('users_count', users_count))
            jurisdictionID = json.loads(body).get('jurisdictionID', jurisdictionID)
            print(jurisdictionID)
         
           
            if users_count > int(os.environ["USERCREATIONLIMIT"]):
                return {
                    'statusCode': 400,
                    'body': json.dumps({'msg':str(os.environ["USERCREATIONLIMIT"])+' max User creation is supported'})
                }
            else:
                if len(jurisdictionID)==0:
                    jurisdictionID = secrets.token_hex(16)
                else:
                    jurisdictionID = jurisdictionID
        
            if users_count<SUBDIVISION:
                data_generator(users_count,jurisdictionID,0)
            else:                
                no_of_loop = users_count/SUBDIVISION
                remaining = users_count%SUBDIVISION
                totalThreads = []
                for i in range(int(no_of_loop)):
                    count = (i+1)*SUBDIVISION
                    if count>SUBDIVISION:
                        count = SUBDIVISION
                    th1 = threading.Thread(target=data_generator, args=(count,jurisdictionID,i))
                    totalThreads.append(th1)
                if(remaining!=0):
                    #for i in range(int(remaining)):
                    th2 = threading.Thread(target=data_generator, args=(int(remaining),jurisdictionID,i))
                    totalThreads.append(th2)
                for thread in totalThreads:
                    print("thread started",thread)
                    thread.start()
                for thread in totalThreads:
                    print("thread join",thread)
                    thread.join()
                #logger.info("no_of_loop %s.", str(no_of_loop))
                #data_generator(int(no_of_loop)*SUBDIVISION,jurisdictionID)
                #if remaining!=0:
                    #logger.info("remaining %s.", str(remaining))
                    #data_generator(int(remaining),jurisdictionID)
       
            return {
                'statusCode': 200,
                'body': json.dumps({'msg':str(users_count) + ' User has been created',"totalIteration":NO_OF_LOOP})
            }
    elif http_method =="DELETE":
        table = dynamodb.Table(os.environ["DATA_TABLE"])
        body = event.get('body')
        jurisdictionID = ''
        internal_userid = ''
        if body is not None:
            jurisdictionID = json.loads(body).get('jurisdictionID', jurisdictionID)
            internal_userid = json.loads(body).get('internal_userid', internal_userid)
            if len(jurisdictionID) == 0 and len(internal_userid) == 0:
                try:
                    with table.batch_writer() as batch:
                        response = table.scan()
                        data = response['Items']
                        if len(data) !=0:
                            while 'LastEvaluatedKey' in response:
                                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                                data.extend(response['Items'])
                            for i in data:
                                # print(i['jurisdictionID'],i['internal_userid'])
                                batch.delete_item(Key={'jurisdictionID': i['jurisdictionID'] ,'internal_userid':i['internal_userid']})
                        else:
                            return {'statusCode': 200,'body': json.dumps({'msg':'Data not found'})}
                    return {'statusCode': 200,'body': json.dumps({'msg':'All data deleted successfully'})}
                except Exception as e:
                    logger.error(e) 
            elif len(internal_userid) == 0:
                try:
                    with table.batch_writer() as batch:
                        response = table.scan(FilterExpression=Attr('jurisdictionID').eq(jurisdictionID))
                        data = response['Items']
                        if len(data) !=0:
                            while 'LastEvaluatedKey' in response:
                                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                                data.extend(response['Items'])
                            for i in data:
                                # print(i['jurisdictionID'],i['internal_userid'])
                                batch.delete_item(Key={'jurisdictionID': i['jurisdictionID'] ,'internal_userid':i['internal_userid']})
                        else:
                            return {'statusCode': 200,'body': json.dumps({'msg':'jurisdictionID not found'})}
                    return {'statusCode': 200,'body': json.dumps({'msg':'Data Deleted successfully for jurisdictionID'})}
                except Exception as e:
                    logger.error(e) 
            else:
                try:
                    response = table.delete_item(Key={'jurisdictionID': jurisdictionID,'internal_userid':internal_userid})
                    return {'statusCode': 200,'body': json.dumps({'msg':'Data Deleted successfully for jurisdictionID'})}
                except:
                    return {'statusCode': 200,'body': json.dumps({'msg': 'Error Occured'})}
        else:
            return {'statusCode': 400,'body': json.dumps({'msg':'Body not None'})} 
        
            
   
