from typing import Any
from enum import Enum
# 
from rest_framework.response import Response

class BaseResponse:

    @staticmethod
    def base_response(succeeded: bool, show: bool, fa_detail: str, en_detail: str, status: int) -> Response:
        return Response(
            data = {
                "succeeded": succeeded,
                "show": show,
                "fa_detail": fa_detail,
                "en_detail": en_detail,
            },
            status = status
        )

    @staticmethod
    def base_response_with_data(succeeded: bool, show: bool, fa_detail: str, en_detail: str, status: int, data: dict) -> Response:
        return Response(
            data = {
                "succeeded": succeeded,
                "show": show,
                "fa_detail": fa_detail,
                "en_detail": en_detail,
                "data": data,
            },
            status = status
        )


class ClientOkResponse:
    SUCCEEDED = True
    STATUS_CODE = 200
    
    @classmethod
    def ok(cls, show: bool = True, fa_detail: str = "", en_detail: str = ""):
        return BaseResponse.base_response(
            succeeded=cls.SUCCEEDED,
            show=show,
            fa_detail=fa_detail,
            en_detail=en_detail,
            status=cls.STATUS_CODE
        )
        

    @classmethod
    def ok_with_data(cls, data: dict, show: bool = True, fa_detail: str = "", en_detail: str = ""):
        return BaseResponse.base_response_with_data(
            succeeded=cls.SUCCEEDED,
            show=show,
            fa_detail=fa_detail,
            en_detail=en_detail,
            status=cls.STATUS_CODE,
            data = data
        )


class ErrorsEnum(Enum):

    INVALID_PARAMETER_FA = "پارمترهای ارسالی معتبر نمیباشد"
    INVALID_PARAMETER_EN = "Invalid paramters"

    NOT_FOUND_FA = "یافت نشد"
    NOT_FOUND_EN = "Not found"
    
    SERIALIZER_ERROR_FA = "خطای اعتبار سنجی"
    SERIALIZER_ERROR_EN = "Validation error"

class ClientErrorResponse:
    
    SUCCEEDED = False
    
    @classmethod
    def invalid_paramter(cls, show: bool = True, fa_detail: str = "", en_detail: str = ""):
        return BaseResponse.base_response(
            succeeded=cls.SUCCEEDED,
            show=show,
            fa_detail=fa_detail if fa_detail else ErrorsEnum.INVALID_PARAMETER_FA.value,
            en_detail=en_detail if en_detail else ErrorsEnum.INVALID_PARAMETER_EN.value,
            status=400,
        )

    @classmethod
    def not_found(cls, show: bool = True, fa_detail: str = "" , en_detail: str=""):
        return BaseResponse.base_response(
            succeeded=cls.SUCCEEDED,
            show=show,
            fa_detail=fa_detail if fa_detail else ErrorsEnum.NOT_FOUND_FA.value,
            en_detail=en_detail if en_detail else ErrorsEnum.NOT_FOUND_EN.value,
            status=404,
        )


    @classmethod
    def serializer_error(cls, show: bool = True, fa_detail: str = "", en_detail: str = ""):
        return BaseResponse.base_response(
            succeeded=cls.SUCCEEDED,
            show=show,
            fa_detail=fa_detail if fa_detail else ErrorsEnum.SERIALIZER_ERROR_FA.value,
            en_detail=en_detail if en_detail else ErrorsEnum.SERIALIZER_ERROR_EN.value,
            status=400,
        )
    
    
    