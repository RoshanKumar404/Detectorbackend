from app import create_app, db
from app.models.municiple import Municipality, Ward

app = create_app()

municipalities_list = [
    # Nagar Parishads
    {"name": "Bishrampur Nagar Parishad", "address": "Bishrampur, Palamu District, Jharkhand", "contact": "06567-222222", "email": "bishrampur.np@jharkhand.gov.in"},
    {"name": "Chakradharpur Nagar Parishad", "address": "Chakradharpur, West Singhbhum District, Jharkhand", "contact": "06587-238222", "email": "chakradharpur.np@jharkhand.gov.in"},
    {"name": "Chaibasa Nagar Parishad", "address": "Chaibasa, West Singhbhum District, Jharkhand", "contact": "06582-256333", "email": "chaibasa.np@jharkhand.gov.in"},
    {"name": "Chatra Nagar Parishad", "address": "Chatra, Chatra District, Jharkhand", "contact": "06545-224444", "email": "chatra.np@jharkhand.gov.in"},
    {"name": "Chirkunda Nagar Parishad", "address": "Chirkunda, Dhanbad District, Jharkhand", "contact": "0326-2525222", "email": "chirkunda.np@jharkhand.gov.in"},
    {"name": "Dumka Nagar Parishad", "address": "Dumka, Dumka District, Jharkhand", "contact": "06434-222222", "email": "dumka.np@jharkhand.gov.in"},
    {"name": "Garhwa Nagar Parishad", "address": "Garhwa, Garhwa District, Jharkhand", "contact": "06561-222222", "email": "garhwa.np@jharkhand.gov.in"},
    {"name": "Godda Nagar Parishad", "address": "Godda, Godda District, Jharkhand", "contact": "06437-222222", "email": "godda.np@jharkhand.gov.in"},
    {"name": "Gumla Nagar Parishad", "address": "Gumla, Gumla District, Jharkhand", "contact": "06524-222222", "email": "gumla.np@jharkhand.gov.in"},
    {"name": "Jhumri Tilaiya Nagar Parishad", "address": "Jhumri Tilaiya, Koderma District, Jharkhand", "contact": "06547-250333", "email": "jhumritilaiya.np@jharkhand.gov.in"},
    {"name": "Jugsalai Nagar Parishad", "address": "Jugsalai, East Singhbhum District, Jharkhand", "contact": "0657-2292222", "email": "jugsalai.np@jharkhand.gov.in"},
    {"name": "Kapali Nagar Parishad", "address": "Kapali, Seraikela Kharsawan District, Jharkhand", "contact": "0657-2303333", "email": "kapali.np@jharkhand.gov.in"},
    {"name": "Lohardaga Nagar Parishad", "address": "Lohardaga, Lohardaga District, Jharkhand", "contact": "06526-224444", "email": "lohardaga.np@jharkhand.gov.in"},
    {"name": "Madhupur Nagar Parishad", "address": "Madhupur, Deoghar District, Jharkhand", "contact": "06438-224444", "email": "madhupur.np@jharkhand.gov.in"},
    {"name": "Mihijam Nagar Parishad", "address": "Mihijam, Jamtara District, Jharkhand", "contact": "06433-228444", "email": "mihijam.np@jharkhand.gov.in"},
    {"name": "Pakur Nagar Parishad", "address": "Pakur, Pakur District, Jharkhand", "contact": "06435-222222", "email": "pakur.np@jharkhand.gov.in"},
    {"name": "Phusro Nagar Parishad", "address": "Phusro, Bokaro District, Jharkhand", "contact": "06549-220444", "email": "phusro.np@jharkhand.gov.in"},
    {"name": "Ramgarh Nagar Parishad", "address": "Ramgarh, Ramgarh District, Jharkhand", "contact": "06553-222222", "email": "ramgarh.np@jharkhand.gov.in"},
    {"name": "Sahibganj Nagar Parishad", "address": "Sahibganj, Sahibganj District, Jharkhand", "contact": "06436-222222", "email": "sahibganj.np@jharkhand.gov.in"},
    {"name": "Simdega Nagar Parishad", "address": "Simdega, Simdega District, Jharkhand", "contact": "06525-224444", "email": "simdega.np@jharkhand.gov.in"},

    # Municipal Corporations
    {"name": "Ranchi Municipal Corporation (RMC)", "address": "Ranchi, Jharkhand", "contact": "0651-2203456", "email": "support@ranchimunicipal.com"},
    {"name": "Dhanbad Municipal Corporation", "address": "Dhanbad, Jharkhand", "contact": "0326-2311222", "email": "dhanbadmc@gmail.com"},
    {"name": "Chas Municipal Corporation", "address": "Chas, Bokaro, Jharkhand", "contact": "06542-265222", "email": "chas.mc@jharkhand.gov.in"},
    {"name": "Deoghar Municipal Corporation", "address": "Deoghar, Jharkhand", "contact": "06432-291222", "email": "deoghar.mc@jharkhand.gov.in"},
    {"name": "Adityapur Municipal Corporation", "address": "Adityapur, Seraikela Kharsawan, Jharkhand", "contact": "0657-2383222", "email": "adityapur.mc@jharkhand.gov.in"},
    {"name": "Mango Municipal Corporation", "address": "Mango, East Singhbhum, Jharkhand", "contact": "0657-2363222", "email": "mango.mc@jharkhand.gov.in"},
    {"name": "Hazaribagh Municipal Corporation", "address": "Hazaribagh, Jharkhand", "contact": "06546-224888", "email": "hazaribagh.mc@jharkhand.gov.in"},
    {"name": "Medininagar Municipal Corporation", "address": "Medininagar, Palamu, Jharkhand", "contact": "06562-224222", "email": "medininagar.mc@jharkhand.gov.in"},
    {"name": "Giridih Municipal Corporation", "address": "Giridih, Jharkhand", "contact": "06532-222888", "email": "giridih.mc@jharkhand.gov.in"}
]

def seed_database():
    with app.app_context():
        print("Starting Database Seeding...")
        
        # Check if municipalities exist
        existing_count = Municipality.query.count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} municipalities. Skipping seeding to prevent duplicate entries.")
            return

        for m_data in municipalities_list:
            # Create Municipality
            m = Municipality(
                municipality_name=m_data["name"],
                municipality_address=m_data["address"],
                municipality_contact=m_data["contact"],
                municipality_email=m_data["email"]
            )
            db.session.add(m)
            db.session.flush() # Flush to get municipality_id
            
            # Create Wards 1 to 10 for each municipality
            for w_num in range(1, 11):
                w = Ward(
                    ward_number=w_num,
                    municipality_id=m.municipality_id
                )
                db.session.add(w)
            
            print(f"Seeded: {m.municipality_name} with Wards 1 to 10.")
        
        db.session.commit()
        print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
