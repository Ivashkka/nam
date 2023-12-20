def send_response(message, user_name):
    print(f"new reply for user {user_name}: {message}")


def wait_for_req():
    user_name = input("user_name: ")
    user_id = input("user_id: ") #for now authorization will be by uuid
    message = input("request: ")
    return {"message": message, "user_name": user_name, "user_id": user_id}
