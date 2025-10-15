mates = {'mateValues': [
    {'mateName': 'wrist_3_joint', 'jsonType': 'Revolute', 'featureId': 'MAAwSflCPC11eLZtK', 'rotationZ': -0.2798873},
    {'mateName': 'wrist_2_joint', 'jsonType': 'Revolute', 'featureId': 'MPK0dohBVMQR4IWPt', 'rotationZ': -1.08561},
    {'mateName': 'shoulder_pan_joint', 'jsonType': 'Revolute', 'featureId': 'MaRcIWoBQm2cpYAQk', 'rotationZ': 0.02886733},
    {'mateName': 'shoulder_lift_joint', 'jsonType': 'Revolute', 'featureId': 'MerKA/NyqIJ7v88mJ', 'rotationZ': -9.769962e-15},
    {'mateName': 'wrist_1_joint', 'jsonType': 'Revolute', 'featureId': 'MfvLXbpG82CcM6fFi', 'rotationZ': 0.2740852},
    {'mateName': 'elbow_joint', 'jsonType': 'Revolute', 'featureId': 'MqCDGHes8xP0FjWzW', 'rotationZ': -0.004972298}]}

for joint in mates['mateValues']:
    mateName = joint['mateName']
    zRot = joint['rotationZ']
    print(f"{mateName} is rotated by: {zRot}")
    
