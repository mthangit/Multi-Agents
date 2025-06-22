# import logging
# import opentracing
# from jaeger_client import Config
# from app.config import settings

# logger = logging.getLogger(__name__)


# def init_tracer():
#     """
#     Initialize Jaeger tracer
#     """
#     if not settings.JAEGER_ENABLED:
#         return None

#     config = Config(
#         config={
#             'sampler': {
#                 'type': 'const',
#                 'param': 1,
#             },
#             'logging': True,
#             'local_agent': {
#                 'reporting_host': settings.JAEGER_HOST,
#                 'reporting_port': settings.JAEGER_PORT,
#             }
#         },
#         service_name='eyevi-backend',
#         validate=True,
#     )

#     # Initialize tracer with a logger
#     tracer = config.initialize_tracer()
#     opentracing.set_global_tracer(tracer)
#     logger.info("Jaeger tracer initialized")
#     return tracer 