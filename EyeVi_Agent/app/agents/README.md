app/
├── agents/
│   ├── search_agent/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent.py                    # Kế thừa từ common.base_agent.BaseAgent
│   │   ├── models.py                   # Pydantic models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── clip_service.py         # Từ Backend/app/models/clip_model.py
│   │   │   ├── milvus_service.py       # Từ Backend/app/database/vector_store.py
│   │   │   ├── search_service.py       # Từ tools/glasses_tool.py
│   │   │   ├── filter_service.py       # Từ tools/glasses_filter_tool.py
│   │   │   └── tool_service.py         # Từ tools/search_tools.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── search_routes.py
│   │   └── configs/
│   │       ├── __init__.py
│   │       └── config.py
│   ├── user_interaction_agent/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent.py                    # Kế thừa từ common.base_agent.BaseAgent
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── request_service.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── user_routes.py
│   │   └── configs/
│   │       ├── __init__.py
│   │       └── config.py
│   ├── order_management_agent/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent.py                    # Kế thừa từ common.base_agent.BaseAgent
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── cart_service.py
│   │   │   └── invoice_service.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── order_routes.py
│   │   └── configs/
│   │       ├── __init__.py
│   │       └── config.py
│   ├── recommendation_agent/            # Tạo mới
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent.py                    # Kế thừa từ common.base_agent.BaseAgent
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── recommend_service.py    # Từ tools/glasses_recommend_tool.py
│   │   │   └── compare_service.py      # Từ tools/glasses_compare_tool.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── recommend_routes.py
│   │   └── configs/
│   │       ├── __init__.py
│   │       └── config.py
├── common/
│   ├── __init__.py
│   ├── base_agent.py                   # Từ Backend/app/agents/base_agent.py
│   ├── base_tool.py                    # Từ tools/base_tool.py
│   ├── a2a_protocol.py
│   └── logging.py
├── data/
│   ├── products.db
│   └── embeddings/
├── scripts/
│   ├── setup_milvus.sh
│   ├── populate_products.py
│   └── run_all.sh
├── tests/
│   ├── __init__.py
│   ├── test_search_agent.py
│   ├── test_order_agent.py
│   ├── test_user_agent.py
│   └── test_recommendation_agent.py
├── docs/
│   ├── api.md
│   └── architecture.md
├── requirements.txt
├── README.md
├── .env
├── .gitignore
└── docker-compose.yml