from typing import List, Optional

from sqlalchemy import CheckConstraint, Enum, Float, ForeignKey, Integer, LargeBinary, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AdditionalData(Base):
    __tablename__ = 'AdditionalData'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    result_name: Mapped[str] = mapped_column(Text, server_default=text('RESULT'))
    result_text: Mapped[str] = mapped_column(Text, server_default=text('""'))
    example_positions: Mapped[str] = mapped_column(Text, server_default=text('"[]"'))
    factor_positions: Mapped[str] = mapped_column(Text, server_default=text('"[]"'))
    result_value_positions: Mapped[str] = mapped_column(Text, server_default=text('"[]"'))
    count: Mapped[str] = mapped_column(Text, server_default=text('\'{"values": {}, "factors": 0}\''))
    result_type: Mapped[Optional[str]] = mapped_column(Text, CheckConstraint("result_type in ('probability', 'confidence')"))
    tree_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary)


class Factor(Base):
    __tablename__ = 'Factor'
    __table_args__ = (
        CheckConstraint('active = 0 or active = 1), value_positions TEXT DEFAULT "[]" NOT NULL'),
    )

    factor_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    text_: Mapped[str] = mapped_column('text', Text, server_default=text('""'))
    active: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    value_positions: Mapped[str] = mapped_column(Text, server_default=text('"[]"'))

    Value: Mapped[List['Value']] = relationship('Value', back_populates='factor', cascade="all, delete, delete-orphan")


class ResultValue(Base):
    __tablename__ = 'ResultValue'

    result_value_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    text_: Mapped[str] = mapped_column('text', Text, server_default=text('""'))

    Example: Mapped[List['Example']] = relationship('Example', back_populates='result_value', cascade="all, delete, delete-orphan")


class Example(Base):
    __tablename__ = 'Example'
    __table_args__ = (
        CheckConstraint('active = 0 or active = 1)'),
    )

    example_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    result_value_id: Mapped[int] = mapped_column(ForeignKey('ResultValue.result_value_id'))
    weight: Mapped[float] = mapped_column(Float)
    active: Mapped[int] = mapped_column(Integer, server_default=text('1'))

    result_value: Mapped['ResultValue'] = relationship('ResultValue', back_populates='Example')
    ExampleFactorValue: Mapped[List['ExampleFactorValue']] = relationship('ExampleFactorValue', back_populates='example', cascade="all, delete, delete-orphan")


class Value(Base):
    __tablename__ = 'Value'

    value_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    factor_id: Mapped[int] = mapped_column(ForeignKey('Factor.factor_id'))
    name: Mapped[str] = mapped_column(Text)
    text_: Mapped[str] = mapped_column('text', Text, server_default=text('""'))

    factor: Mapped['Factor'] = relationship('Factor', back_populates='Value')
    ExampleFactorValue: Mapped[List['ExampleFactorValue']] = relationship('ExampleFactorValue', back_populates='value', cascade="all, delete, delete-orphan")


class ExampleFactorValue(Base):
    __tablename__ = 'ExampleFactorValue'

    example_factor_value_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    example_id: Mapped[int] = mapped_column(ForeignKey('Example.example_id'))
    value_id: Mapped[int] = mapped_column(ForeignKey('Value.value_id'))

    example: Mapped['Example'] = relationship('Example', back_populates='ExampleFactorValue')
    value: Mapped['Value'] = relationship('Value', back_populates='ExampleFactorValue')
