"""
  " SPDX-License-Identifier: AGPL-3.0-or-later
  "
  " Litbrown Creator Assistant
  " Automation Software for Magic: the Gathering Online (TM) Content Creators
  " Copyright (C) 2026 Reid Litbrown
  "
  " This program is free software: you can redistribute it and/or modify
  " it under the terms of the GNU Affero General Public License as published
  " by the Free Software Foundation, either version 3 of the License, or
  " (at your option) any later version.
  "
  " This program is distributed in the hope that it will be useful,
  " but WITHOUT ANY WARRANTY; without even the implied warranty of
  " MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  " GNU Affero General Public License for more details.
  "
  " You should have received a copy of the GNU Affero General Public License
  " along with this program.  If not, see <https://www.gnu.org/licenses/>.
  "
  """

import collections.abc
import contextlib
import copy
import dataclasses
import datetime
import typing

from loguru import logger
import pydantic

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..Config import *
from ..I18n import *

class LCATableModel [T: pydantic.BaseModel] (QAbstractTableModel):
	
	__QT_ROLES = (Qt.DisplayRole, Qt.EditRole)
	
	__model_class: type[T]
	__model_reference: list[T] | None = None
	__model_reference_factory: typing.Callable[[], list[T]]
	__context_manager: typing.ContextManager | typing.Callable[[], typing.ContextManager]
	__columns: tuple[str]
	
	def __init__ (self,
		model_class: type[T],
		model_reference_factory: list[dict] | None = None,
		context_manager: typing.ContextManager | typing.Callable[[], typing.ContextManager] | None = None,
		*args, **kwargs
	):
		super().__init__(*args, **kwargs)
		self.__model_class = model_class
		if not model_reference_factory:
			self.__model_reference = []
		self.__model_reference_factory = model_reference_factory or (lambda : self.__model_reference)
		self.__context_manager = context_manager if context_manager is not None else contextlib.nullcontext()
		self.__columns = tuple(self.__determine_columns(self.__model_class, [], ''))
		logger.debug(self.__columns)
		logger.debug(self.__model_reference)

	def __determine_columns (self, reference: type[T], columns: list, base: str) -> list:
		for field_name, field_info in reference.model_fields.items():
			# Handle Union type hints: e.g. str | None
			annotation = getattr(field_info.annotation, '__args__', [field_info.annotation])[0]
			if (isinstance(field_info.annotation, type) and not issubclass(field_info.annotation, list)) and issubclass(annotation, pydantic.BaseModel):
				self.__determine_columns( annotation, columns, f'{base}{'.' if base else ''}{field_name}' )
			else:
				columns.append(f'{base}{'.' if base else ''}{field_name}')
		return columns

	def __ctx (self) -> typing.ContextManager:
		return self.__context_manager() if callable(self.__context_manager) else self.__context_manager

	def qmodelindex (self, index: collections.abc.Sequence[int, str]) -> QModelIndex:
		if len(index) != 2 or type(index[0]) != int or type(index[1]) != str:
			raise ValueError(f'Bad pseudo-index passed: {index}')
		return self.createIndex(index[0], self.get_column_index(index[1]))

	def data (self,
		index: QModelIndex | collections.abc.Sequence[int, str],
		role: int = Qt.DisplayRole,
	) -> object:
		if issubclass(type(index), collections.abc.Sequence):
			index = self.qmodelindex(index)
		if role in self.__QT_ROLES:
			row = self.__model_reference_factory()[index.row()]
			path = self.__columns[index.column()]
			reference, attr = self.__reduce_path(row, path)
			return getattr(reference, attr)

	def setData (self,
		index: QModelIndex | collections.abc.Sequence[int, str],
		value: object,
		role: int = Qt.EditRole,
	) -> bool:
		if issubclass(type(index), collections.abc.Sequence):
			index = self.qmodelindex(index)
		if role in self.__QT_ROLES:
			row = self.__model_reference_factory()[index.row()]
			path = self.__columns[index.column()]
			reference, attr = self.__reduce_path(row, path)
			if getattr(reference, attr) == value:
				logger.debug(f'aborting assignment | row {index.row()} col {path}')
				return True
			logger.debug(f'model[{index.row()}][{path}] = {value}')
			with self.__ctx():
				setattr(reference, attr, value)
			self.dataChanged.emit(index, index)
			logger.debug(self.__model_reference_factory())
			return True
		return False

	def __reduce_path (self, reference: pydantic.BaseModel, path: str) -> tuple[pydantic.BaseModel, str]:
		reduced_path = path.split('.', 1)
		if len(reduced_path) > 1:
			return self.__reduce_path( getattr(reference, reduced_path[0]), reduced_path[1] )
		else:
			return reference, path

	def rowCount (self, index: QModelIndex | None = None) -> int:
		return len(self.__model_reference_factory())

	def columnCount (self, index: QModelIndex | None = None) -> int:
		return len(self.__columns)

	def insertRows (self, row: int, count: int, parent: QModelIndex | None = None, *, model_args: dict = {}) -> bool:
		logger.debug(f'Inserting {count} rows at pos {row}')
		self.beginInsertRows(parent or QModelIndex(), row, row + count - 1)
		with self.__ctx():
			for _ in range(count):
				self.__model_reference_factory().insert(row, self.__model_class(**model_args))
		self.endInsertRows()
		return True

	def removeRows (self, row: int, count: int, parent: QModelIndex | None = None) -> bool:
		self.beginRemoveRows(parent or QModelIndex(), row, row + count - 1)
		with self.__ctx():
			for _ in range(count):
				del self.__model_reference_factory()[row]
		self.endRemoveRows()
		return True

	def moveRow (self, from_index: int, to_index: int, parent: QModelIndex | None = None) -> bool:
		with self.__ctx():
			self.__model_reference_factory().insert( to_index, self.__model_reference_factory().pop(from_index) )
		return True

	def get_column_names (self) -> tuple:
		return self.__columns

	def get_column_index (self, name: str) -> int:
		try:
			return self.get_column_names().index(name)
		except ValueError:
			logger.error(f'Column not found: {name}')
			raise

	def get_data_reference (self) -> list[T]:
		logger.debug(self.__model_reference_factory())
		return self.__model_reference_factory()

